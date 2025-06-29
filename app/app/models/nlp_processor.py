"""
NLP processor for intelligent conversation handling in the Smart Learning with Personalized AI Tutor application
"""

import json
import re
import numpy as np
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import requests
import os
import tempfile
import base64
import logging
import speech_recognition as sr
from gtts import gTTS
from app.models.ai_model import AIModelType

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class NLPProcessor:
    """NLP processor for intelligent conversation handling"""
    
    def __init__(self, model_path=None):
        """
        Initialize the NLP processor
        
        Args:
            model_path (str): Path to the NLP model
        """
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Initialize sentiment analysis pipeline
        try:
            self.sentiment_analyzer = pipeline("sentiment-analysis")
        except:
            # Fallback to a simpler approach if transformers not available
            self.sentiment_analyzer = None
            
        # Initialize named entity recognition
        try:
            self.ner = pipeline("ner")
        except:
            self.ner = None
            
        # Initialize question answering
        try:
            self.qa = pipeline("question-answering")
        except:
            self.qa = None
            
        # Load subject-specific knowledge base
        self.knowledge_base = self._load_knowledge_base()
        
        # TF-IDF vectorizer for topic extraction
        self.vectorizer = TfidfVectorizer(max_features=1000)
        
        # Learning style adaptation parameters
        self.learning_style_keywords = {
            "visual": ["see", "look", "view", "appear", "show", "picture", "image", "diagram"],
            "auditory": ["hear", "listen", "sound", "tell", "discuss", "explain", "talk"],
            "reading_writing": ["read", "write", "note", "list", "text", "document", "book"],
            "kinesthetic": ["do", "feel", "touch", "hold", "experience", "practice", "try", "experiment"]
        }
        
        # Speech recognition for voice interactions
        self.recognizer = sr.Recognizer()
        
        # Initialize model handlers
        self.model_handlers = {
            AIModelType.GPT: self._handle_gpt_model,
            AIModelType.BERT: self._handle_bert_model,
            AIModelType.LLAMA: self._handle_llama_model,
            AIModelType.CLAUDE: self._handle_claude_model,
            AIModelType.CUSTOM: self._handle_custom_model
        }
    
    def preprocess_text(self, text):
        """
        Preprocess text for NLP tasks
        
        Args:
            text (str): Text to preprocess
            
        Returns:
            list: List of preprocessed tokens
        """
        # Tokenize
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in self.stop_words]
        
        return tokens
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            float: Sentiment score (-1.0 to 1.0)
        """
        if self.sentiment_analyzer:
            result = self.sentiment_analyzer(text)
            if result[0]['label'] == 'POSITIVE':
                return result[0]['score']
            else:
                return -result[0]['score']
        else:
            # Simple fallback sentiment analysis
            positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "helpful", "clear", "understand", "thanks"]
            negative_words = ["bad", "poor", "terrible", "confusing", "unclear", "difficult", "hard", "not", "don't", "cannot"]
            
            tokens = self.preprocess_text(text)
            positive_count = sum(1 for token in tokens if token in positive_words)
            negative_count = sum(1 for token in tokens if token in negative_words)
            
            total = positive_count + negative_count
            if total == 0:
                return 0.0
            
            return (positive_count - negative_count) / total
    
    def extract_topics(self, text):
        """
        Extract topics from text
        
        Args:
            text (str): Text to extract topics from
            
        Returns:
            list: List of topics
        """
        tokens = self.preprocess_text(text)
        
        # Count token frequencies
        token_counts = Counter(tokens)
        
        # Get the most common tokens as topics
        topics = [topic for topic, count in token_counts.most_common(5) if len(topic) > 3]
        
        return topics

    def speech_to_text(self, audio_data):
        """
        Convert speech to text
        
        Args:
            audio_data (bytes): Audio data
            
        Returns:
            str: Transcribed text
        """
        try:
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            # Process with speech recognition
            with sr.AudioFile(temp_audio_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
            
            # Clean up temporary file
            os.unlink(temp_audio_path)
            
            return text
        except Exception as e:
            logging.error(f"Speech recognition error: {str(e)}")
            return ""
    
    def text_to_speech(self, text, lang='en'):
        """
        Convert text to speech
        
        Args:
            text (str): Text to convert
            lang (str): Language code
            
        Returns:
            bytes: Audio data
        """
        try:
            # Generate speech
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                tts.save(temp_audio.name)
                temp_audio_path = temp_audio.name
            
            # Read audio data
            with open(temp_audio_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up temporary file
            os.unlink(temp_audio_path)
            
            return audio_data
        except Exception as e:
            logging.error(f"Text to speech error: {str(e)}")
            return None
    
    def generate_personalized_response(self, user_message, user_profile, conversation_history=None, ai_model=None, ai_model_preference=None):
        """
        Generate a personalized response based on user message and profile
        
        Args:
            user_message (str): User's message
            user_profile (dict): User's profile data
            conversation_history (list): Previous conversations
            ai_model (AIModel): AI model to use for generation
            ai_model_preference (UserAIModelPreference): User's AI model preferences
            
        Returns:
            str: Personalized response
        """
        # Extract topics from user message
        topics = self.extract_topics(user_message)
        
        # Find relevant information from knowledge base
        relevant_info = self._find_relevant_information(user_message, topics)
        
        # If an AI model is specified, use it for response generation
        if ai_model:
            try:
                # Get handler for the model type
                handler = self.model_handlers.get(ai_model.model_type)
                if handler:
                    # Call the appropriate handler with model details
                    response = handler(
                        user_message=user_message,
                        user_profile=user_profile,
                        conversation_history=conversation_history,
                        ai_model=ai_model,
                        ai_model_preference=ai_model_preference,
                        relevant_info=relevant_info
                    )
                    if response:
                        return response
            except Exception as e:
                logging.error(f"Error using AI model {ai_model.name}: {str(e)}")
                # Fall back to default processing
        
        # Default processing if no model specified or model processing failed
        # Adapt response based on learning style
        learning_style = user_profile.get('learning_style', 'reading_writing')
        
        if learning_style == 'visual':
            response = self._adapt_for_visual_learner(relevant_info)
        elif learning_style == 'auditory':
            response = self._adapt_for_auditory_learner(relevant_info)
        elif learning_style == 'reading_writing':
            response = self._adapt_for_reading_writing_learner(relevant_info)
        elif learning_style == 'kinesthetic':
            response = self._adapt_for_kinesthetic_learner(relevant_info)
        else:
            response = self._generate_default_response(relevant_info)
        
        # Adjust response based on skill level
        skill_level = user_profile.get('skill_level', 5)
        response = self._adjust_for_skill_level(response, skill_level)
        
        # Adjust response length based on preference
        response_time_preference = user_profile.get('response_time_preference', 5)
        response = self._adjust_response_length(response, response_time_preference)
        
        return response
    
    def _handle_gpt_model(self, user_message, user_profile, conversation_history, ai_model, ai_model_preference, relevant_info):
        """Handle GPT model API calls"""
        try:
            # Get API key from user preference or config
            api_key = None
            if ai_model_preference and ai_model_preference.api_key:
                api_key = ai_model_preference.api_key
            else:
                from app.config import Config
                api_key = Config.OPENAI_API_KEY
            
            if not api_key:
                return None
            
            # Get custom parameters if available
            custom_params = {}
            if ai_model_preference and ai_model_preference.custom_parameters:
                custom_params = json.loads(ai_model_preference.custom_parameters)
            
            # Prepare context from conversation history
            context = ""
            if conversation_history:
                for conv in conversation_history[-5:]:  # Last 5 conversations
                    context += f"User: {conv['user_message']}\nAI: {conv['ai_response']}\n"
            
            # Prepare messages
            messages = [
                {"role": "system", "content": f"You are an educational AI assistant helping a user with {user_profile.get('preferred_subjects', 'various subjects')}. "
                                             f"The user's learning style is {user_profile.get('learning_style', 'unknown')}. "
                                             f"Their skill level is {user_profile.get('skill_level', 5)}/10."},
                {"role": "user", "content": f"{context}\n\nUser question: {user_message}"}
            ]
            
            # Add relevant information
            if relevant_info:
                messages.append({"role": "system", "content": f"Relevant information: {relevant_info}"})
            
            # Set up API parameters
            params = {
                "model": "gpt-3.5-turbo",  # Default model
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
            }
            
            # Override with custom parameters
            params.update(custom_params)
            
            # Make API request
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.post(
                ai_model.api_endpoint or "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=params
            )
            
            response_data = response.json()
            if response.status_code == 200 and "choices" in response_data:
                return response_data["choices"][0]["message"]["content"]
            
            logging.error(f"GPT API error: {response_data}")
            return None
            
        except Exception as e:
            logging.error(f"Error in GPT model processing: {str(e)}")
            return None
            
    def _handle_bert_model(self, user_message, user_profile, conversation_history, ai_model, ai_model_preference, relevant_info):
        """Handle BERT model for response generation"""
        try:
            # Implement BERT-specific logic here
            # For now, use a simple implementation with the Hugging Face pipeline
            if not self.qa:
                return None
                
            # Use question answering if relevant info is available
            if relevant_info:
                answer = self.qa(question=user_message, context=relevant_info)
                return answer['answer']
                
            return None
        except Exception as e:
            logging.error(f"Error in BERT model processing: {str(e)}")
            return None
            
    def _handle_llama_model(self, user_message, user_profile, conversation_history, ai_model, ai_model_preference, relevant_info):
        """Handle Llama model API calls"""
        # Similar to GPT but with Llama-specific API parameters
        try:
            # Get API key from user preference or config
            api_key = None
            if ai_model_preference and ai_model_preference.api_key:
                api_key = ai_model_preference.api_key
            else:
                from app.config import Config
                api_key = Config.LLAMA_API_KEY
                
            if not api_key:
                return None
                
            # Call Llama API with appropriate parameters
            # Implementation depends on the specific Llama API being used
            return None  # Placeholder
        except Exception as e:
            logging.error(f"Error in Llama model processing: {str(e)}")
            return None
            
    def _handle_claude_model(self, user_message, user_profile, conversation_history, ai_model, ai_model_preference, relevant_info):
        """Handle Claude model API calls"""
        try:
            # Get API key from user preference or config
            api_key = None
            if ai_model_preference and ai_model_preference.api_key:
                api_key = ai_model_preference.api_key
            else:
                from app.config import Config
                api_key = Config.ANTHROPIC_API_KEY
                
            if not api_key:
                return None
                
            # Prepare context
            context = ""
            if conversation_history:
                for conv in conversation_history[-5:]:
                    context += f"Human: {conv['user_message']}\nAssistant: {conv['ai_response']}\n"
                    
            # Make API request to Claude
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
            
            # Get custom parameters
            custom_params = {}
            if ai_model_preference and ai_model_preference.custom_parameters:
                custom_params = json.loads(ai_model_preference.custom_parameters)
                
            # Build request
            request_data = {
                "model": "claude-2.0",  # Default model
                "prompt": f"{context}\n\nHuman: {user_message}\n\nAssistant:",
                "max_tokens_to_sample": 500,
                "temperature": 0.7
            }
            
            # Override with custom parameters
            request_data.update(custom_params)
            
            # Make request
            response = requests.post(
                ai_model.api_endpoint or "https://api.anthropic.com/v1/complete",
                headers=headers,
                json=request_data
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data.get("completion", "")
                
            logging.error(f"Claude API error: {response.text}")
            return None
            
        except Exception as e:
            logging.error(f"Error in Claude model processing: {str(e)}")
            return None
            
    def _handle_custom_model(self, user_message, user_profile, conversation_history, ai_model, ai_model_preference, relevant_info):
        """Handle custom model API calls"""
        try:
            # Get API endpoint and parameters from the model
            api_endpoint = ai_model.api_endpoint
            if not api_endpoint:
                return None
                
            # Get API key if needed
            api_key = None
            if ai_model.api_key_required and ai_model_preference and ai_model_preference.api_key:
                api_key = ai_model_preference.api_key
                
            # Get model parameters
            model_params = {}
            if ai_model.parameters:
                model_params = json.loads(ai_model.parameters)
                
            # Override with user's custom parameters if available
            if ai_model_preference and ai_model_preference.custom_parameters:
                user_params = json.loads(ai_model_preference.custom_parameters)
                model_params.update(user_params)
                
            # Prepare request data
            request_data = {
                "message": user_message,
                "user_profile": user_profile,
                "conversation_history": conversation_history,
                **model_params
            }
            
            # Set up headers
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                
            # Make API request
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=request_data
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if "response" in response_data:
                    return response_data["response"]
                    
            logging.error(f"Custom model API error: {response.text}")
            return None
            
        except Exception as e:
            logging.error(f"Error in custom model processing: {str(e)}")
            return None
    
    def calculate_engagement_score(self, user_message):
        """
        Calculate user engagement score based on message
        
        Args:
            user_message (str): User's message
            
        Returns:
            float: Engagement score (0.0 to 1.0)
        """
        # Factors that indicate engagement
        factors = {
            'message_length': min(len(user_message) / 100, 1.0),  # Normalize to 0-1
            'question_marks': min(user_message.count('?') * 0.2, 1.0),  # Questions indicate engagement
            'exclamation_marks': min(user_message.count('!') * 0.1, 0.5),  # Excitement
            'follow_up_indicators': 0.0  # Words that indicate follow-up interest
        }
        
        # Check for follow-up indicators
        follow_up_words = ["more", "another", "example", "explain", "understand", "clarify", "continue"]
        tokens = self.preprocess_text(user_message)
        factors['follow_up_indicators'] = min(sum(1 for token in tokens if token in follow_up_words) * 0.2, 1.0)
        
        # Calculate overall engagement score
        weights = {
            'message_length': 0.3,
            'question_marks': 0.3,
            'exclamation_marks': 0.1,
            'follow_up_indicators': 0.3
        }
        
        engagement_score = sum(factors[key] * weights[key] for key in factors)
        
        return min(engagement_score, 1.0)
    
    def _load_knowledge_base(self):
        """
        Load knowledge base from file
        
        Returns:
            dict: Knowledge base
        """
        try:
            with open('app/models/knowledge_base.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return a simple default knowledge base
            return {
                "subjects": {
                    "math": {
                        "algebra": "Algebra is a branch of mathematics dealing with symbols and the rules for manipulating these symbols.",
                        "calculus": "Calculus is the mathematical study of continuous change.",
                        "geometry": "Geometry is a branch of mathematics that studies the sizes, shapes, positions, and dimensions of things."
                    },
                    "science": {
                        "physics": "Physics is the natural science that studies matter, its motion and behavior through space and time.",
                        "chemistry": "Chemistry is the scientific discipline involved with elements and compounds.",
                        "biology": "Biology is the natural science that studies life and living organisms."
                    },
                    "programming": {
                        "python": "Python is an interpreted, high-level, general-purpose programming language.",
                        "java": "Java is a class-based, object-oriented programming language.",
                        "javascript": "JavaScript is a programming language that conforms to the ECMAScript specification."
                    }
                }
            }
    
    def _find_relevant_information(self, user_message, topics):
        """
        Find relevant information from knowledge base
        
        Args:
            user_message (str): User's message
            topics (list): Extracted topics
            
        Returns:
            dict: Relevant information
        """
        relevant_info = {}
        
        # Search through knowledge base for relevant information
        for subject, subject_data in self.knowledge_base.get("subjects", {}).items():
            for topic, info in subject_data.items():
                # Check if any extracted topic matches
                if any(extracted_topic in topic.lower() for extracted_topic in topics):
                    if subject not in relevant_info:
                        relevant_info[subject] = {}
                    relevant_info[subject][topic] = info
                
                # Also check if topic is directly mentioned in user message
                if topic.lower() in user_message.lower():
                    if subject not in relevant_info:
                        relevant_info[subject] = {}
                    relevant_info[subject][topic] = info
        
        return relevant_info
    
    def _adapt_for_visual_learner(self, relevant_info):
        """
        Adapt response for visual learners
        
        Args:
            relevant_info (dict): Relevant information
            
        Returns:
            str: Adapted response
        """
        response = "Let me show you visually:\n\n"
        
        for subject, topics in relevant_info.items():
            response += f"## {subject.capitalize()}\n\n"
            
            for topic, info in topics.items():
                response += f"### {topic.capitalize()}\n"
                response += f"{info}\n\n"
                response += "I would recommend looking at diagrams or videos about this topic. Visualizing the concepts will help you understand them better.\n\n"
        
        if not relevant_info:
            response += "I don't have specific visual information on this topic yet. Would you like me to find some diagrams or visual explanations for you?"
        
        return response
    
    def _adapt_for_auditory_learner(self, relevant_info):
        """
        Adapt response for auditory learners
        
        Args:
            relevant_info (dict): Relevant information
            
        Returns:
            str: Adapted response
        """
        response = "Let me explain this to you:\n\n"
        
        for subject, topics in relevant_info.items():
            response += f"About {subject}:\n\n"
            
            for topic, info in topics.items():
                response += f"When we talk about {topic}, here's what it means:\n"
                response += f"{info}\n\n"
                response += "Try saying this out loud to yourself to remember it better. Discussing this with others would also help reinforce your understanding.\n\n"
        
        if not relevant_info:
            response += "I don't have specific information on this topic yet. Would you like me to explain the basic concepts verbally?"
        
        return response
    
    def _adapt_for_reading_writing_learner(self, relevant_info):
        """
        Adapt response for reading/writing learners
        
        Args:
            relevant_info (dict): Relevant information
            
        Returns:
            str: Adapted response
        """
        response = "Here's a detailed explanation:\n\n"
        
        for subject, topics in relevant_info.items():
            response += f"# {subject.capitalize()}\n\n"
            
            for topic, info in topics.items():
                response += f"## {topic.capitalize()}\n"
                response += f"{info}\n\n"
                response += "Key points to note:\n"
                # Extract key points from info
                sentences = info.split('.')
                for i, sentence in enumerate(sentences[:3]):
                    if sentence.strip():
                        response += f"- {sentence.strip()}.\n"
                response += "\nTry writing these points down in your own words to better understand and remember them.\n\n"
        
        if not relevant_info:
            response += "I don't have specific textual information on this topic yet. Would you like me to provide some reading materials or written explanations?"
        
        return response
    
    def _adapt_for_kinesthetic_learner(self, relevant_info):
        """
        Adapt response for kinesthetic learners
        
        Args:
            relevant_info (dict): Relevant information
            
        Returns:
            str: Adapted response
        """
        response = "Let's learn by doing:\n\n"
        
        for subject, topics in relevant_info.items():
            response += f"For {subject}, here are some hands-on activities:\n\n"
            
            for topic, info in topics.items():
                response += f"To understand {topic}:\n"
                response += f"{info}\n\n"
                response += "Try this practical exercise:\n"
                
                if "math" in subject.lower():
                    response += "- Work through some example problems step by step\n"
                    response += "- Create your own problems and solve them\n"
                elif "science" in subject.lower():
                    response += "- Design a simple experiment to demonstrate this concept\n"
                    response += "- Build a model that represents this idea\n"
                elif "programming" in subject.lower():
                    response += "- Write a small program that implements this concept\n"
                    response += "- Debug and modify existing code to see how it works\n"
                else:
                    response += "- Create a project that applies this knowledge\n"
                    response += "- Teach this concept to someone else using examples\n"
                
                response += "\nLearning by doing will help you internalize these concepts better.\n\n"
        
        if not relevant_info:
            response += "I don't have specific hands-on activities for this topic yet. Would you like me to suggest some practical exercises or projects?"
        
        return response
    
    def _generate_default_response(self, relevant_info):
        """
        Generate default response when learning style is not specified
        
        Args:
            relevant_info (dict): Relevant information
            
        Returns:
            str: Default response
        """
        response = "Here's what I know about this topic:\n\n"
        
        for subject, topics in relevant_info.items():
            response += f"## {subject.capitalize()}\n\n"
            
            for topic, info in topics.items():
                response += f"### {topic.capitalize()}\n"
                response += f"{info}\n\n"
        
        if not relevant_info:
            response += "I don't have specific information on this topic yet. Could you provide more details about what you'd like to learn?"
        
        return response
    
    def _adjust_for_skill_level(self, response, skill_level):
        """
        Adjust response based on user's skill level
        
        Args:
            response (str): Original response
            skill_level (int): User's skill level (1-10)
            
        Returns:
            str: Adjusted response
        """
        if skill_level <= 3:
            # Beginner: Simplify language, add more explanations
            response = response.replace("complex", "step-by-step")
            response = "Let's start with the basics:\n\n" + response
            response += "\n\nDon't worry if this seems challenging at first. We'll take it one step at a time."
        elif skill_level <= 7:
            # Intermediate: Standard response
            pass
        else:
            # Advanced: Add more technical details
            response = "Given your advanced understanding, here's a detailed explanation:\n\n" + response
            response += "\n\nFor a deeper dive into this topic, you might want to explore the underlying principles and advanced applications."
        
        return response
    
    def _adjust_response_length(self, response, preference):
        """
        Adjust response length based on user preference
        
        Args:
            response (str): Original response
            preference (int): User's preference (1-10, 1=quick, 10=detailed)
            
        Returns:
            str: Adjusted response
        """
        if preference <= 3:
            # User prefers quick responses
            paragraphs = response.split('\n\n')
            if len(paragraphs) > 3:
                # Keep only the first few paragraphs
                short_response = '\n\n'.join(paragraphs[:3])
                short_response += "\n\n(I've provided a concise answer. Let me know if you'd like more details.)"
                return short_response
        elif preference >= 8:
            # User prefers detailed responses
            response += "\n\nSince you prefer detailed explanations, here are some additional insights:\n\n"
            response += "- The concepts we've discussed connect to broader themes in this field\n"
            response += "- Understanding these principles will help you tackle more advanced topics\n"
            response += "- Consider exploring related concepts to deepen your knowledge"
        
        return response 