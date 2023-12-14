import streamlit as st
import requests
from bs4 import BeautifulSoup
import yfinance as yf

def get_user_input():
    st.sidebar.header("Please Enter Investment Requirements")
    total_fund_value = st.sidebar.number_input("Total fund available", min_value=0, step=1)
    percentage_of_funds = st.sidebar.slider("Percentage of funds to be invested", 0, 100, 50, 1)
    risk_level = st.sidebar.radio("Risk Appetite", ["Low", "Medium", "High"])
    tenure = st.sidebar.radio("Tenure of Investment", ["Short", "Long"])

    submit_button = st.sidebar.button("Submit")
    bal=(total_fund_value*percentage_of_funds)*0.01

    user_input = [bal, risk_level, tenure, submit_button]
    return user_input

def get_url_based_on_risk(risk_level):
    if(risk_level == "Low"):
        return "https://groww.in/mutual-funds/top/best-low-risk-mutual-funds"
    elif(risk_level == "Medium"):
        return "https://groww.in/mutual-funds/top/best-moderate-risk-mutual-funds"
    else:
        return "https://groww.in/mutual-funds/top/best-high-risk-mutual-funds"


def scrape_url(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the table with a 'th' tag containing 'Fund Name'
        fund_name_table = None
        for table in soup.find_all('table'):
            th_element = table.find_all('th', text='Fund Name', limit=1)
            if th_element:
                fund_name_table = table
                break

        # Check if the table is found
        if fund_name_table:
            # Find the index of the 'Fund Name' column
            fund_name_index = None
            headers = fund_name_table.find('tr').find_all('th')
            for i, header in enumerate(headers):
                if 'Fund Name' in header.get_text():
                    fund_name_index = i
                    break

            # Check if 'Fund Name' is found in the table headers
            if fund_name_index is not None:
                # Find the first entry in the 'Fund Name' column
                rows = fund_name_table.find_all('tr')
                if len(rows) > 1:  # Check if there is at least one row (excluding header)
                    first_entry = rows[1].find_all('td')[fund_name_index]

                    # Find the anchor tag and get its href attribute
                    anchor_tag = first_entry.find('a')
                    if anchor_tag:
                        part_url = anchor_tag.get('href')
                        full_url=f"https://groww.in"+part_url
                        return full_url
                    else:
                        return "No anchor tag found for the first entry in the 'Fund Name' column."
                else:
                    return "No data rows found in the table."
            else:
                return "No 'Fund Name' column found in the table."
        else:
            return "No table found with a 'th' tag containing 'Fund Name'."
    else:
        return f"Failed to retrieve the webpage. Status code: {response.status_code}"
    
def get_stock_value(stock_name):
    try:
        stock = yf.Ticker(stock_name)
        current_value = stock.history(period='1d')['Close'].iloc[-1]
        return current_value
    except Exception as e:
        print(f"Failed to fetch stock value for {stock_name}. Error: {e}")
        return None
    
def scrape_another_url(url, fund):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the table containing the header 'Name'
        target_table = None
        for table in soup.find_all('table'):
            header_row = table.find('tr')
            if header_row and header_row.find('th', text='Name'):
                # Check if 'Assets' header is present in the table
                assets_header = table.find('th', text='Assets')
                if assets_header:
                    target_table = table
                    break

        # If the target table is found, extract data
        if target_table:
            data = []
            # Find all rows in the table (skip the header row)
            for row in target_table.find_all('tr')[1:]:
                # Extract 'Name' and 'Assets' values
                columns = row.find_all('td')
                
                if len(columns) >= 2:  # Ensure there are at least two columns
                    name = columns[0].text.strip()
                    assets_index = header_row.find_all('th').index(assets_header)
                    assets_str = columns[assets_index].text.strip()

                    # Convert percentage string to float
                    try:
                        assets = float(assets_str.rstrip('%'))
                    except ValueError:
                        print(f"Failed to convert '{assets_str}' to a float.")
                        assets = None

                    # Calculate Investment Amount and Number of Stocks
                    if assets is not None:
                        investment_amount = assets * 0.01 * fund
                        stock_value = get_stock_value(name)
                        if stock_value is not None:
                            number_of_stocks = int(investment_amount // stock_value)
                        else:
                            number_of_stocks = 0


                        # Store the data in a dictionary
                        data.append({
                            'Stock': name,
                            'Weightage': assets,
                            'Investment Amount': investment_amount,
                            'Stock Value': stock_value,
                            'Number of Stocks': number_of_stocks
                        })
                else:
                    print("Row does not have enough columns.")

            return data
        else:
            print("Table with headers 'Name' and 'Assets' not found.")
    else:
        print(f"Failed to fetch the page. Status code: {response.status_code}")

def main():

    user_input = get_user_input()

    if user_input[-1]:  # Check if the submit button is clicked
        # Display loading sign while processing
        st.title("Recommended Portfolio")
        with st.spinner("Processing..."):

            # Store obtained parameters
            bal, risk, tenure = user_input[:3]

            # Get URL based on risk
            url = get_url_based_on_risk(risk)

            # Scraping content from the picked URL
            new_url = scrape_url(url)

            # Scraping content from another singular URL
            content_array = scrape_another_url(new_url, bal)

        # Display results to the user
        st.success("Processing completed!")
        st.write("The Stocks obtained are:")
        st.table(content_array)
    else:
        st.title("Find Your Perfect Portfolio!")
        st.warning("Please enter information on the sidebar and then click 'Submit'.")

if __name__ == "__main__":
    main()
