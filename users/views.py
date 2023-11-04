from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from underthesea import word_tokenize, sent_tokenize
from sklearn.metrics.pairwise import cosine_similarity
from django.shortcuts import redirect
from heapq import nlargest
import os
from google.cloud import vision, texttospeech
from dj_rest_auth.views import LoginView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import status
from rest_framework import viewsets, mixins
from .models import PostCheck
from .serializers import PostCheckSerializer
from .constants import ALLOWED_EXTENSIONS
from string import punctuation
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser
from rest_framework.renderers import JSONRenderer
from collections import defaultdict
from django.views.generic import ListView
from rest_framework.permissions import IsAdminUser, AllowAny
from sklearn.feature_extraction.text import TfidfVectorizer

current_directory = os.path.dirname(os.path.abspath(__file__))


class PostCheckViews(viewsets.ModelViewSet):
    queryset = PostCheck.objects.order_by("created_at")
    serializer_class = PostCheckSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["POST"], url_path="update-status")
    def update_status(self, request, pk=None):
        news = self.get_object()
        news.status = request.data.get("status") == "True"
        news.save()
        return redirect("demo")


class PostCommunityViews(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    APIView for receive news of client
    """

    queryset = PostCheck.objects.order_by("created_at")
    serializer_class = PostCheckSerializer


class NewsListView(ListView):
    queryset = PostCheck.objects.order_by("-created_at")
    paginate_by = 20
    template_name = "demo.html"


class RecommendView(APIView):
    """
    APIView for recommend news for client
    """

    parser_classes = [MultiPartParser]
    renderer_classes = [JSONRenderer]
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="content",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="News content",
            )
        ]
    )
    def post(self, request):
        new_content = request.data.get("content")
        existing_posts = PostCheck.objects.filter(status=True)

        # Compare new content with existing content and find similar records
        similar_posts = []

        for post in existing_posts:
            similarity = self.similar_percentage(new_content, post.content)
            if similarity >= 70:
                similar_posts.append(
                    {
                        "post": PostCheckSerializer(post).data,
                        "similarity_percentage": similarity,
                    }
                )

        return Response({"similar_posts": similar_posts}, status=status.HTTP_200_OK)

    def similar_percentage(self, text1, text2):
        # Create a TF-IDF vectorizer
        vectorizer = TfidfVectorizer()

        # Vectorize the texts
        tfidf_matrix = vectorizer.fit_transform([text1, text2])

        # Compute cosine similarity
        cosine_similarities = cosine_similarity(tfidf_matrix)

        # Get the similarity percentage
        similarity_percentage = cosine_similarities[0][1] * 100

        return similarity_percentage


class DetectTextView(APIView):
    parser_classes = [MultiPartParser]
    renderer_classes = [JSONRenderer]

    @swagger_auto_schema(
        operation_description="Upload file to detect text",
        manual_parameters=[
            openapi.Parameter(
                name="file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Upload file",
            )
        ],
    )
    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response(
                {"message": "No file part in the request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file.name == "":
            return Response(
                {"message": "No file selected for uploading"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file and self.allowed_file(file.name):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
                current_directory, "certificate.json"
            )
            client = vision.ImageAnnotatorClient()
            content = file.read()
            image = vision.Image(content=content)
            response = client.text_detection(image=image)
            texts = response.text_annotations
            my_list = [text.description for text in texts]
            result = my_list.pop(0)
            result = result.replace("\n", " ")
            result = result.strip()
            return Response(result)

        else:
            return Response(
                {"message": "Allowed file types are png, jpg, jpeg, gif"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def allowed_file(self, filename):
        return (
            "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        )


class SummaryText(APIView):
    parser_classes = [MultiPartParser]
    renderer_classes = [JSONRenderer]

    @swagger_auto_schema(
        operation_description="Summary Text",
        manual_parameters=[
            openapi.Parameter(
                name="text",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="Text for Summary",
            )
        ],
    )
    def post(self, request):
        text = request.POST.get("text")
        text = text.replace("\n", " ")
        text = text.strip()
        file_path = os.path.join(current_directory, "vn-stopword.txt")
        with open(file_path, encoding="utf-8") as file:
            stopwords = [word.rstrip() for word in file.readlines()]

        word_freq = defaultdict(int)
        for word in word_tokenize(text):
            if word.lower() not in stopwords and word.lower() not in punctuation:
                word_freq[word] += 1

        max_freq = max(word_freq.values())
        word_freq = {word: freq / max_freq for word, freq in word_freq.items()}

        senc_scores = defaultdict(int)
        for sent in sent_tokenize(text):
            senc_scores[sent] = sum(
                word_freq.get(word, 0) for word in word_tokenize(sent)
            )

        select_len = int(len(sent_tokenize(text)) * 0.25)

        summary = nlargest(select_len, senc_scores, key=senc_scores.get)
        return Response({"text": " ".join(summary)})


class TextToSpeech(APIView):
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_description="Text to Speech",
        manual_parameters=[
            openapi.Parameter(
                name="text",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="Text to Speech",
            )
        ],
    )
    def post(self, request):
        # Get the text from the request data
        text = request.data.get("text")
        output_filename = "tts.mp3"
        responsehttp = HttpResponse()

        if text:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
                current_directory, "certificate.json"
            )
            client = texttospeech.TextToSpeechClient()

            input_text = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="vi-VN", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            # Perform the text-to-speech request
            response = client.synthesize_speech(
                input=input_text, voice=voice, audio_config=audio_config
            )
            # Save the audio to a file
            with open(output_filename, "wb") as out:
                out.write(response.audio_content)

            # Read the audio content from the saved file
            with open(output_filename, "rb") as audio_file:
                audio_content = audio_file.read()

            responsehttp.write(audio_content)
            responsehttp["Content-Type"] = "audio/mp3"
            responsehttp["Content-Length"] = os.path.getsize(output_filename)

            os.remove(output_filename)
        return responsehttp


class CustomLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response(
                {"message": "User is already logged in."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.request = request
        self.serializer = self.get_serializer(data=self.request.data)
        self.serializer.is_valid(raise_exception=True)

        self.login()
        return self.get_response()
