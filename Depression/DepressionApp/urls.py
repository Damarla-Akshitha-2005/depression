from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    # Root URL — redirect to home page
    path("", RedirectView.as_view(url="/index.html", permanent=False)),

    path("index.html", views.index, name="index"),
    path("Register.html", views.Register, name="Register"),
    path("Signup", views.Signup, name="Signup"),
    path("Login.html", views.Login, name="Login"),
    path("UserLogin", views.UserLogin, name="UserLogin"),
    path("SearchFriends.html", views.SearchFriends, name="SearchFriends"),
    path("UploadPost.html", views.UploadPost, name="UploadPost"),
    path("UploadPostData", views.UploadPostData, name="UploadPostData"),
    path("AdminLogin", views.AdminLogin, name="AdminLogin"),
    path("Admin.html", views.Admin, name="Admin"),
    path("ViewUsers.html", views.ViewUsers, name="ViewUsers"),
    path("ViewPosts.html", views.ViewPosts, name="ViewPosts"),
    path("SendMotivatedPost.html", views.SendMotivatedPost, name="SendMotivatedPost"),
    path("SendMotivatedPostData", views.SendMotivatedPostData, name="SendMotivatedPostData"),
    path("ViewMotivatedPost.html", views.ViewMotivatedPost, name="ViewMotivatedPost"),
    path("MotivatedText.html", views.MotivatedText, name="MotivatedText"),
    path("Chatbot.html", views.Chatbot, name="Chatbot"),
    path("ChatBotResponse", views.ChatBotResponse, name="ChatBotResponse"),
    
    # New Experience Sharing Routes
    path("ShareExperience.html", views.ShareExperience, name="ShareExperience"),
    path("SaveExperience", views.SaveExperience, name="SaveExperience"),
    path("BrowseExperiences.html", views.BrowseHelpfulExperiences, name="BrowseExperiences"),
    
    # User Profile & Deletion
    path("UserProfile.html", views.UserProfile, name="UserProfile"),
    path("DeletePost", views.DeletePost, name="DeletePost"),
    path("DeleteExperience", views.DeleteExperience, name="DeleteExperience"),
]
