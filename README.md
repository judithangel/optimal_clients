# find(IQ) potential customers
## What this code does
TL;DR: It suggests companies which people from sales could contact next.
You can upload an excel file with data from companies including:

- Account Name
- Last Modified Date
- Industry
- Annual Revenue Currency
- Annual Revenue
- Employees

This data can then be used to find the number of job advertisements for service technicians or similar positions from these companies by web scraping.
The app also performs clustering, shows which of our current customers belong to which cluster and suggests top ten companies out of a chosen cluster based on the number of job ads.
Additionally, the distribution of different industries among the scraped data and the total top ten companies with service technician job ads are being displayed.

### Requirements
All required python modules can be installed via 'requirements.txt'.
In case you want to use the scraper, installation of a chrome driver is needed.
