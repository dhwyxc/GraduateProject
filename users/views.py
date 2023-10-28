import os
from google.cloud import vision, texttospeech
from dj_rest_auth.views import LoginView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import status
from rest_framework import viewsets
from .models import PostCheck
from .serializers import PostCheckSerializer
from rest_framework.exceptions import PermissionDenied
from .constants import ALLOWED_EXTENSIONS
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from underthesea import word_tokenize, sent_tokenize
from heapq import nlargest
from string import punctuation
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser
from rest_framework.renderers import JSONRenderer
from collections import defaultdict
from django.views.generic import ListView
from django.shortcuts import redirect

current_directory = os.path.dirname(os.path.abspath(__file__))
class PostCheckViews(viewsets.ModelViewSet):
    queryset = PostCheck.objects.order_by('created_at')
    serializer_class = PostCheckSerializer
    
    @action(detail=True, methods=['POST'], url_path="update-status")
    def update_status(self, request, pk=None):
        user = self.request.user
        
        if user.is_staff:
            news = self.get_object()
            status = request.data.get('status') == 'True' 
            news.status = status
            news.save()
            return redirect('demo')
        else:
            raise PermissionDenied(detail='Not have permission')
        
class NewsListView(ListView):
    queryset = PostCheck.objects.order_by('-created_at')
    paginate_by = 20
    template_name = 'demo.html'
    
class CustomLoginView(LoginView):
        
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:  
            return Response({"message": "User is already logged in."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        self.request = request
        self.serializer = self.get_serializer(data=self.request.data)
        self.serializer.is_valid(raise_exception=True)

        self.login()
        return self.get_response()
    
class UploadView(APIView):
    parser_classes = [MultiPartParser]
    renderer_classes = [JSONRenderer]
    
    @swagger_auto_schema(
        operation_description='Upload file to detect text',
        manual_parameters=[
            openapi.Parameter(
                name='file',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description='Upload file'
            )
        ]
    )
    def post(self, request):
        file = request.FILES.get('file')
        
        if not file:
            return Response({'message': 'No file part in the request'}, status=status.HTTP_400_BAD_REQUEST)

        if file.name == '':
            return Response({'message': 'No file selected for uploading'}, status=status.HTTP_400_BAD_REQUEST)

        if file and self.allowed_file(file.name):
            
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(current_directory, 'certificate.json')
            client = vision.ImageAnnotatorClient()
            content = file.read()
            image = vision.Image(content=content)
            response = client.text_detection(image=image)
            texts = response.text_annotations
            my_list = [text.description for text in texts]
            result = my_list.pop(0)
            result = result.replace('\n', ' ')
            result = result.strip()
            return Response(result)

        else:
            return Response({'message': 'Allowed file types are png, jpg, jpeg, gif'}, status=status.HTTP_400_BAD_REQUEST)
        
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class SummaryText(APIView):
    parser_classes = [MultiPartParser]
    renderer_classes = [JSONRenderer]
    
    @swagger_auto_schema(
        operation_description='Summary Text',
        manual_parameters=[
            openapi.Parameter(
                name='text',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description='Text for Summary'
            )
        ]
    )
    def post(self,request):
        
        text = request.POST.get('text')
        text = text.replace('\n', ' ')
        text = text.strip()
        file_path = os.path.join(current_directory, 'vn-stopword.txt')
        with open(file_path, encoding='utf-8') as file:
            stopwords = [word.rstrip() for word in file.readlines()]
        
        word_freq = defaultdict(int)
        for word in word_tokenize(text):
            if word.lower() not in stopwords and word.lower() not in punctuation:
                word_freq[word] += 1
    
        max_freq = max(word_freq.values())
        word_freq = {word: freq / max_freq for word, freq in word_freq.items()}

        senc_scores = defaultdict(int)
        for sent in sent_tokenize(text):
            senc_scores[sent] = sum(word_freq.get(word, 0) for word in word_tokenize(sent))
                        
        select_len = int(len(sent_tokenize(text)) * 0.25)

        summary = nlargest(select_len, senc_scores, key = senc_scores.get)
        return Response({"text": " ".join(summary)})
    
class TextToSpeech(APIView):
    
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'text': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ))
    def post(self, request):
        # Get the text from the request data
        text = request.data.get('text')
        output_filename = 'tts.mp3'
        responsehttp = HttpResponse()
        
        if text:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(current_directory, 'certificate.json')    
            client = texttospeech.TextToSpeechClient()

            input_text = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="vi-VN",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
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
            responsehttp['Content-Type'] ='audio/mp3'
            responsehttp['Content-Length'] = os.path.getsize(output_filename)
            
            os.remove(output_filename)
        return responsehttp