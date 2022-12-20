from dash import Dash, html, dcc, Output, Input

import plotly.graph_objects as go
import pandas as pd

import pandas as pd
import sqlite3

import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Dash(__name__)
server = app.server

con = sqlite3.connect("hr")


data_employee_title = pd.read_sql("SELECT employees.first_name, jobs.job_title " +
                                  "FROM employees " +
                                  "INNER JOIN jobs ON employees.job_id " +
                                  "= jobs.job_id", con)


def extract_data_from_website():
    URL = "https://www.itjobswatch.co.uk/jobs/uk/sqlite.do"
    table = BeautifulSoup(requests.get(URL).content, 'html5lib').find(
        'table', attrs={'class': 'summary'})
    table.find('form').decompose()
    table_data = table.tbody.find_all("tr")
    table = []
    for i in table_data:
        row = []
        inner_row = i.find_all("td")
        if len(inner_row) == 0:
            inner_row = i.find_all("th")
        for j in inner_row:
            row.append(j.text)
        table.append(row)

    hd = table[1]
    hd[0] = "index"
    employee_sal = pd.read_sql("SELECT employees.salary " +
                               "FROM employees", con)
    avg_salary = employee_sal['salary'].mean()
    df = pd.DataFrame(table)
    df.drop(index=[0, 1, 2, 3, 4, 5, 6, 7, 10,
            11, 14, 15], axis=0, inplace=True)
    df.columns = hd
    df.set_index("index", inplace=True)
    df.reset_index(inplace=True)
    df['Same period 2021'] = df['Same period 2021'].str.replace('£', '')
    df['Same period 2021'] = df['Same period 2021'].str.replace(',', '')
    df['Same period 2021'] = df['Same period 2021'].str.replace(
        '-', '0').astype(float)
    df['6 months to19 Dec 2022'] = df['6 months to19 Dec 2022'].str.replace(
        '£', '')
    df['6 months to19 Dec 2022'] = df['6 months to19 Dec 2022'].str.replace(
        ',', '').astype(float)
    df['Same period 2020'] = df['Same period 2020'].str.replace('£', '')
    df['Same period 2020'] = df['Same period 2020'].str.replace(
        ',', '').astype(float)

    df.loc[4] = ['Average', avg_salary, avg_salary, avg_salary]

    return df


extracted_data_from_website = extract_data_from_website()
axis = extracted_data_from_website["index"]
extracted_data_from_website.drop("index", inplace=True, axis=1)
years = extracted_data_from_website.columns


job_count = data_employee_title.groupby('job_title').count().reset_index()
job_count.columns = ["Job Title", "Count"]
jobs = job_count["Job Title"]

jobs_salary_main = pd.read_sql(
    "SELECT job_title, min_salary, max_salary FROM jobs", con)
jobs_salary_main.drop(index=0, axis=0, inplace=True)
jobs_salary_main["difference"] = jobs_salary_main["max_salary"] - \
    jobs_salary_main["min_salary"]

jobs_salary = jobs_salary_main


def update_jobs_selected(list_of_jobs):
    global job_count
    job_count = data_employee_title.groupby('job_title').count().reset_index()
    job_count.columns = ["Job Title", "Count"]

    if list_of_jobs != "all" and len(list_of_jobs) != 0:
        job_count = job_count[job_count["Job Title"].isin(list_of_jobs)]


def update_difference(minimum, maximum):
    global jobs_salary
    global jobs_salary_main
    jobs_salary = jobs_salary_main
    diff = maximum - minimum
    jobs_salary = jobs_salary[jobs_salary["difference"] <= diff]


def update_year(year):
    return extracted_data_from_website[year]

    #


app.layout = html.Div(
    id="root",
    children=[

        html.Div(
            id="app-container",
            # className="row",
            children=[
                # Column for user controls
                # Banner display
                html.Div(
                    id="banner",
                    children=[
                        html.H2("DASH - CALLS ANALYSIS", id="title"),
                    ],
                ),
                html.Div(
                    # className="nine columns div-for-charts bg-grey",
                    id="image",
                    children=[
                       dcc.Graph(id="output1"),
                       dcc.Graph(id="output2"),
                       dcc.Graph(id="output3"),

                    ],
                ),
            ],
        ),

        html.Div(
            id="sidebar",
            # className="three columns div-user-controls",
            children=[
                # Filter
                html.Div(

                    className="div-for-dropdown",
                    children=[
                        html.H1("Final exam dashboard"),
                        dcc.Dropdown(jobs,
                                     multi=True,
                                     value='all',
                                     placeholder="All",
                                     id="input1"
                                     ),
                    ],
                ),
                # Change to side by side for mobile layout
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                html.P("States:"),
                                dcc.Slider(0, 30000, 1000,
                                           value=1000,
                                           id='minimum'
                                           ),
                                            dcc.Slider(0, 30000, 1000,
                   value=20000,
                   id='maximum'
                   ),

                            ],
                        ),
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                html.P("Dates"),

                                dcc.Dropdown(years,

                                             value='all',
                                             placeholder="6 months to19 Dec 2022",
                                             id="years"
                                             ),

                            ],
                        ),
                    ],
                ),
            ],
        ),

    ]
)


@app.callback(
    Output('output1', 'figure'),

    Input('input1', 'value')
)
def outputreboot(value1):

    update_jobs_selected(value1)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=job_count["Job Title"], y=job_count["Count"])
                  )
    return fig


@app.callback(
    Output('output2', 'figure'),
    [
        Input('minimum', 'value'),
        Input('maximum', 'value'),
    ]
)
def outputreboot(value1, value2):

    # update_jobs_selected(value1)
    update_difference(value1, value2)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=jobs_salary["difference"], y=jobs_salary["job_title"], orientation="h"))

    return fig


@app.callback(
    Output('output3', 'figure'),
    Input('years', 'value')
)
def outputreboot(value1):
    if value1 == "all" or value1 == None:
        y = extracted_data_from_website["6 months to19 Dec 2022"]
    else:
        y = update_year(value1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=axis.values, y=y.values))

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
