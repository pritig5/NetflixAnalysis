import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Title and Description
st.title("Netflix Viewing Activity Analysis")
st.write(
    """
This app allows you to analyze your Netflix viewing activity.
"""
)

# File Upload
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    # Load data
    df = pd.read_csv(uploaded_file)
    st.write("Shape of the dataset:", df.shape)
    st.write("Data Information:", df.info())
    st.write(df.head())

    # Data Cleaning
    df_copy = df.copy()
    df = df[df["Supplemental Video Type"].isna()]
    df = df.drop(
        columns=["Supplemental Video Type", "Bookmark", "Latest Bookmark", "Country"]
    )

    def extract_text(title):
        if ":" in title:
            return title.split(":")[0].strip()
        else:
            return title.strip()

    df["Processed Title"] = df["Title"].apply(extract_text)
    df["datetime"] = pd.to_datetime(df["Start Time"])
    df["Start Time"] = pd.to_datetime(df["Start Time"])
    df["date"] = df["datetime"].dt.date
    df["time"] = df["datetime"].dt.time
    df["day"] = df["datetime"].dt.day_name()
    df["month"] = df["datetime"].dt.month_name()
    df["year"] = df["datetime"].dt.year
    df["Start Time"] = df["Start Time"].apply(
        lambda x: x.strftime("%Y-%m-%d, %H:00:00")
    )
    df["duration_min"] = (
        df["Duration"].str.split(":").apply(lambda x: int(x[0]) * 60 + int(x[1]))
    )
    df = df[df["duration_min"] >= 2]

    # Data Visualization of Profiles
    st.write("## Viewing Frequency of Each Profile")
    profile_count = df["Profile Name"].value_counts()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(profile_count.index, profile_count.values, color="teal")
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_xlabel("Profile Name", fontsize=12)
    ax.set_title("Viewing Frequency of Each Profile", fontsize=15)
    st.pyplot(fig)

    # Duration Analysis
    df_duration = df[["Profile Name", "duration_min"]]

    def categorize_duration(x):
        if x < 15:
            return "less than 15 mins"
        elif x < 30:
            return "less than 30 mins"
        elif x < 60:
            return "less than 60 mins"
        else:
            return "more than 1 hour"

    df_duration["duration_cats"] = df_duration["duration_min"].apply(
        categorize_duration
    )
    durations_count = df_duration["duration_cats"].value_counts()

    # Assuming durations_count is defined earlier
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(durations_count.index, durations_count.values, color="purple")
    ax.set_xlabel("Duration categories", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title("Durations of Viewing Activity", fontsize=14)
    ax.tick_params(axis="both", which="major", labelsize=10)
    st.pyplot(fig)

    st.write("## Stacked Bar Chart for Duration Categories by Profile")
    df_duration.groupby(["Profile Name", "duration_cats"]).size().unstack().plot(
        kind="bar", stacked=True
    )
    plt.title("Duration of Viewing Activity")
    plt.legend(loc=(1.05, 0))
    st.pyplot(plt)

    # Selective Profile Analysis
    st.write("## Selective Profile Analysis")
    unique_profiles = df["Profile Name"].unique()
    profile = st.selectbox("Select a profile", unique_profiles)

    df_filtered = df[df["Profile Name"] == profile]
    unique_devices = df_filtered["Device Type"].unique()

    num_devices = st.slider(
        "How many devices are there for this profile?",
        min_value=1,
        max_value=len(unique_devices),
        value=1,
    )

    selected_devices = st.multiselect(
        "Select devices", unique_devices, default=unique_devices[:num_devices]
    )

    device_data = [
        df_filtered[df_filtered["Device Type"] == device] for device in selected_devices
    ]
    if device_data:
        df_combined = pd.concat(device_data)
        csv_filename = f"{profile}_data.csv"
        df_combined.to_csv(csv_filename, index=False)
        st.write(
            f"Data for profile '{profile}' with selected devices exported to '{csv_filename}'"
        )
        st.write(f"Shape of combined data: {df_combined.shape}")

        by_hour = df_combined["Start Time"].value_counts().sort_index(ascending=True)
        by_hour.index = pd.to_datetime(by_hour.index)
        df_datehour = by_hour.rename_axis("date_hour").reset_index(name="counts")
        idx = pd.date_range(min(by_hour.index), max(by_hour.index), freq="1H")
        s = by_hour.reindex(idx, fill_value=0)
        dfs_count = s.rename_axis("datetime").reset_index(name="freq")
        dfs_count["date"] = dfs_count["datetime"].dt.date
        dfs_count["hour"] = dfs_count["datetime"].dt.hour
        dfs_count["day"] = dfs_count["datetime"].dt.day_name()
        dfs_count["month"] = dfs_count["datetime"].dt.month
        dfs_count["year"] = dfs_count["datetime"].dt.year
        dfs_count = dfs_count.drop(["datetime"], axis=1)
        dfs_hm = dfs_count[["day", "hour", "freq"]].groupby(["day", "hour"]).sum()
        m = dfs_hm.unstack().fillna(0)
        hours_list = list(range(0, 24))
        days_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        sns.set_context("talk")
        f, ax = plt.subplots(figsize=(12, 5))
        ax = sns.heatmap(
            m,
            linewidths=0.5,
            ax=ax,
            yticklabels=days_name,
            xticklabels=hours_list,
            cmap="viridis_r",
        )
        ax.set_title("Heatmap of My Netflix Viewing Activity", fontsize=20, y=1.02)
        ax.set_xlabel("Hour of day", fontsize=12)
        ax.set_ylabel("Day of Week", fontsize=12)
        ax.tick_params(axis="both", which="major", labelsize=10)
        st.pyplot(f)

        # Provide Tableau Public embed code here
        tableau_embed_code = """<div class='tableauPlaceholder' id='viz1720513827896' style='position: relative'><noscript><a href='#'><img alt=' ' src='https:&#47;&#47;public.tableau.com&#47;static&#47;images&#47;Ne&#47;Netflix_report_17204413655820&#47;Dashboard1&#47;1_rss.png' style='border: none' /></a></noscript><object class='tableauViz'  style='display:none;'><param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' /> <param name='embed_code_version' value='3' /> <param name='site_root' value='' /><param name='name' value='Netflix_report_17204413655820&#47;Dashboard1' /><param name='tabs' value='yes' /><param name='toolbar' value='yes' /><param name='static_image' value='https:&#47;&#47;public.tableau.com&#47;static&#47;images&#47;Ne&#47;Netflix_report_17204413655820&#47;Dashboard1&#47;1.png' /> <param name='animate_transition' value='yes' /><param name='display_static_image' value='yes' /><param name='display_spinner' value='yes' /><param name='display_overlay' value='yes' /><param name='display_count' value='yes' /><param name='language' value='en-US' /></object></div>                <script type='text/javascript'>                    var divElement = document.getElementById('viz1720513827896');                    var vizElement = divElement.getElementsByTagName('object')[0];                    if ( divElement.offsetWidth > 800 ) { vizElement.style.width='100%';vizElement.style.height=(divElement.offsetWidth*0.75)+'px';} else if ( divElement.offsetWidth > 500 ) { vizElement.style.width='100%';vizElement.style.height=(divElement.offsetWidth*0.75)+'px';} else { vizElement.style.width='100%';vizElement.style.minHeight='1800px';vizElement.style.maxHeight=(divElement.offsetWidth*1.77)+'px';}                     var scriptElement = document.createElement('script');                    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';                    vizElement.parentNode.insertBefore(scriptElement, vizElement);                </script>"""

        # Display embedded Tableau Public dashboard
        st.write("## Embedded Tableau Public Dashboard")
        st.markdown(tableau_embed_code, unsafe_allow_html=True)

        # Remove CSV file after displaying results
        os.remove(csv_filename)
else:
    st.write("Please upload a CSV file to proceed.")

import streamlit as st
import streamlit.components.v1 as components

st.title("Tableau Dashboard")

    tableau_code = """
    <div class='tableauPlaceholder' id='viz1720513827896' style='position: relative'>
        <noscript>
            <a href='#'>
                <img alt=' ' src='https://public.tableau.com/static/images/Ne/Netflix_report_17204413655820/Dashboard1/1_rss.png' style='border: none' />
            </a>
        </noscript>
        <object class='tableauViz' style='display:none;'>
            <param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' />
            <param name='embed_code_version' value='3' />
            <param name='site_root' value='' />
            <param name='name' value='Netflix_report_17204413655820/Dashboard1' />
            <param name='tabs' value='yes' />
            <param name='toolbar' value='yes' />
            <param name='static_image' value='https://public.tableau.com/static/images/Ne/Netflix_report_17204413655820/Dashboard1/1.png' />
            <param name='animate_transition' value='yes' />
            <param name='display_static_image' value='yes' />
            <param name='display_spinner' value='yes' />
            <param name='display_overlay' value='yes' />
            <param name='display_count' value='yes' />
            <param name='language' value='en-US' />
        </object>
    </div>
    <script type='text/javascript'>
        var divElement = document.getElementById('viz1720513827896');
        var vizElement = divElement.getElementsByTagName('object')[0];
        if (divElement.offsetWidth > 800) {
            vizElement.style.width='100%';
            vizElement.style.height=(divElement.offsetWidth*0.75)+'px';
        } else if (divElement.offsetWidth > 500) {
            vizElement.style.width='100%';
            vizElement.style.height=(divElement.offsetWidth*0.75)+'px';
        } else {
            vizElement.style.width='100%';
            vizElement.style.minHeight='1800px';
            vizElement.style.maxHeight=(divElement.offsetWidth*1.77)+'px';
        }
        var scriptElement = document.createElement('script');
        scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';
        vizElement.parentNode.insertBefore(scriptElement, vizElement);
    </script>
    """

    # Embed the Tableau code into Streamlit using components.html
    components.html(tableau_code, height=800)


    
