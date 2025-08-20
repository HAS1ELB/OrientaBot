"""
Chat handling and API interaction module
"""
import json
import re
import streamlit as st
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS

class ChatHandler:
    def __init__(self):
        """Initialize the chat handler with Groq client"""
        if not GROQ_API_KEY:
            st.error("⌚ GROQ_API_KEY manquant. Configurez votre .env file avec votre clé API Groq.")
            st.stop()
        
        self.client = Groq(api_key=GROQ_API_KEY)
    
    def stream_response(self, messages, temperature=0.7):
        """Stream chat response from Groq"""
        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=MAX_TOKENS,
                stream=True,
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Erreur: {str(e)}"
    
    def extract_json_recommendations(self, text):
        """Extract JSON recommendations if present"""
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        return None
    
    def process_chat_input(self, prompt, system_prompt, temperature):
        """Process user input and generate response"""
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            # Prepare messages for API
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(st.session_state.messages)
            
            # Stream response
            response_placeholder = st.empty()
            full_response = ""
            
            for chunk in self.stream_response(messages, temperature):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # Add assistant message to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Check for JSON recommendations
            recommendations = self.extract_json_recommendations(full_response)
            if recommendations:
                with st.expander("📊 Recommandations structurées"):
                    st.json(recommendations)
            
            return full_response