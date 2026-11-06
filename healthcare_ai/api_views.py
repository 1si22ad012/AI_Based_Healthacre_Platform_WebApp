from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import analyze_symptoms, chatbot_answer


class SymptomAssessmentApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data or {}
        analysis = analyze_symptoms(data)
        return Response(analysis, status=status.HTTP_200_OK)


class ChatbotApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message = (request.data or {}).get("message", "")
        conversation_id = (request.data or {}).get("conversation_id")
        from .models import ChatConversation

        conversation = None
        if conversation_id:
            conversation = ChatConversation.objects.filter(id=conversation_id, user=request.user).first()
        response, sources, conversation = chatbot_answer(message, request.user, conversation)
        return Response({"response": response, "sources": sources, "conversation_id": conversation.id}, status=status.HTTP_200_OK)