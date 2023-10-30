import os
import requests
import json
import yfinance as yf
from yahooquery import Ticker
import openai
import streamlit as st
import matplotlib.pyplot as plt
import cons


# Get an OpenAI API Key before continuing
if "openai_api_key" in st.secrets:
    openai_api_key = st.secrets.openai_api_key
else:
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", key = "openai.api_key")
if not openai_api_key:
    st.title("Hello, I'm Income Statement Analyzer 👓")
    st.info("Enter an OpenAI API Key to continue")
    st.info("If you are not sure on how to get your OpenAI API key:")
    st.info( " 1) Please visit https://platform.openai.com/account/api-keys")
    st.info(" 2) Click on 'Create new key' and copy and save the key in a safe location")
    st.stop()
      
os.environ["SERPAPI_API_KEY"] = cons.SERPAPI_API_KEY    

st.subheader("Successfully entered API Key")
