
# Solar Power Price Checker

Electricity prices nowadays can vary a lot during the summer days and sometimes selling the generated power from our solar plantations comes at a loss. In order to deal with the fluctuation of the prices I have come up with an idea to track them hour by hour automatically thanks to Python.

The project has been developed using Python, BeautifulSoup and Selenium and it requires a computer or a virtual machine to run the software 24/7.

The software is mostly hardcoded for a friend of mine who uses it, however it has the potential to become market-friendly and to be automated.




## How it works
The process is really simple. The software goes to IBEX website and checks current hour prices. If the price of electricity this hour is lower than or equal to a variable set by the user in a JSON config file it goes to Huawei Inverters system and sets the power outage to the grid to 0. (And if the price is above the set price, it sets the power outage to the grid to a preset ammount set in a JSON file by the user).

After that it checks the time left to the next hour and puts the software to sleep until the new hour has come up and checks everything again. 

The software has a few security measures set to not blow up the program, such as:
- Automatic checks for internet connection
- Check if the target website servers are running(If not enter an endless loop until they are back online)

## Future Improvements

- On the first run automatically inspect the user solar plantation and generate a config file for each inverter and a variable for power usage.
- Automatically save hourly log with messages from each function in the software and send it via email to the user to monitor proper functioning.
- Application could be made into a Web Application customized for each user if the project ever gets released to the market.
## Authors

- [@htoskov](https://www.github.com/htoskov)

