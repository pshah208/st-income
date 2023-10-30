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
      
os.environ["SERPAPI_API_KEY"] = env.SERPAPI_API_KEY    

st.subheader("Successfully entered API Key")
openai.api_key = openai_api_key

def get_company_news(company_name):
    params = {
        "engine": "google",
        "tbm": "nws",
        "q": company_name,
        "api_key": os.environ["SERPAPI_API_KEY"],
    }

    response = requests.get('https://serpapi.com/search', params=params)
    data = response.json()

    return data.get('news_results')


def write_news_to_file(news, filename):
    with open(filename, 'w') as file:
        for news_item in news:
            if news_item is not None:
                title = news_item.get('title', 'No title')
                link = news_item.get('link', 'No link')
                date = news_item.get('date', 'No date')
                file.write(f"Title: {title}\n")
                file.write(f"Link: {link}\n")
                file.write(f"Date: {date}\n\n")



def get_stock_evolution(company_name, period="1y"):
    # Get the stock information
    stock = yf.Ticker(company_name)

    # Get historical market data
    hist = stock.history(period=period)

    # Convert the DataFrame to a string with a specific format
    data_string = hist.to_string()

    # Append the string to the "investment.txt" file
    with open("investment.txt", "a") as file:
        file.write(f"\nStock Evolution for {company_name}:\n")
        file.write(data_string)
        file.write("\n")

    # Return the DataFrame
    return hist


def get_financial_statements(ticker):
    # Create a Ticker object
    company = Ticker(ticker)

    # Get financial data
    balance_sheet = company.balance_sheet().to_string()
    cash_flow = company.cash_flow(trailing=False).to_string()
    income_statement = company.income_statement().to_string()
    valuation_measures = str(company.valuation_measures)  # This one might already be a dictionary or string

    # Write data to file
    with open("investment.txt", "a") as file:
        file.write("\nBalance Sheet\n")
        file.write(balance_sheet)
        file.write("\nCash Flow\n")
        file.write(cash_flow)
        file.write("\nIncome Statement\n")
        file.write(income_statement)
        file.write("\nValuation Measures\n")
        file.write(valuation_measures)




def get_data(company_name, company_ticker, period="1y", filename="investment.txt"):
    news = get_company_news(company_name)
    if news:
        write_news_to_file(news, filename)
    else:
        print("No news found.")

    hist = get_stock_evolution(company_ticker)

    get_financial_statements(company_ticker)

    return hist


def financial_analyst(request):
    print(f"Received request: {request}")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{
            "role":
            "user",
            "content":
            f"Given the user request, what is the comapany name and the company stock ticker ?: {request}?"
        }],
        functions=[{
            "name": "get_data",
            "description":
            "Get financial data on a specific company for investment purposes",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type":
                        "string",
                        "description":
                        "The name of the company",
                    },
                    "company_ticker": {
                        "type":
                        "string",
                        "description":
                        "the ticker of the stock of the company"
                    },
                    "period": {
                        "type": "string",
                        "description": "The period of analysis"
                    },
                    "filename": {
                        "type": "string",
                        "description": "the filename to store data"
                    }
                },
                "required": ["company_name", "company_ticker"],
            },
        }],
        function_call={"name": "get_data"},
    )

    message = response["choices"][0]["message"]

    if message.get("function_call"):
        # Parse the arguments from a JSON string to a Python dictionary
        arguments = json.loads(message["function_call"]["arguments"])
        print(arguments)
        company_name = arguments["company_name"]
        company_ticker = arguments["company_ticker"]

        # Parse the return value from a JSON string to a Python dictionary
        hist = get_data(company_name, company_ticker)
        print(hist)

        with open("investment.txt", "r") as file:
            content = file.read()[:14000]

        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "user",
                    "content": request
                },
                message,
                {
                    "role": "system",
                    "content": """write a detailled investment thesis to answer
                      the user request as a html document. Provide numbers to justify
                      your assertions, a lot ideally. Provide
                     a recommendation to buy the stock of the company
                     or not given the information available, but also give disclaimer on how 
                     the data can change based on any new news and risks of investment."""
                },
                {
                    "role": "assistant",
                    "content": content,
                },
            ],
        )

        return (second_response["choices"][0]["message"]["content"], hist)

#Setup Streamlit frontend
from stanalysis import financial_analyst

def main():
    st.title("GenAI stock analyzer")

    company_name = st.text_input("Company name:", key='company_name')
    analyze_button = st.button("Analyze")

    if analyze_button:
        if company_name:
            st.write("Analyzing... Please wait.")

            investment_thesis, hist = financial_analyst(company_name)

            # Select 'Open' and 'Close' columns from the hist dataframe
            hist_selected = hist[['Open', 'Close']]

            # Create a new figure in matplotlib
            fig, ax = plt.subplots()

            # Plot the selected data
            hist_selected.plot(kind='line', ax=ax)

            # Set the title and labels
            ax.set_title(f"{company_name} Stock Price")
            ax.set_xlabel("Date")
            ax.set_ylabel("Stock Price")

            # Display the plot in Streamlit
            st.pyplot(fig)

            st.write("Investment Thesis / Recommendation:")

            st.markdown(investment_thesis, unsafe_allow_html=True)
        else:
            st.write("Please enter the company name.")


if __name__ == "__main__":
    main()