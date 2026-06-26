import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(
    page_title="K.K's Book App",
    page_icon="logo.jpeg",
    layout="wide"
)
# ---------------- FILES ----------------
UNREAD_FILE = "unread_books.csv"
READ_FILE = "read_books.csv"
SAVINGS_FILE = "savings_books.csv"
WRITTEN_FILE = "written_books.csv"

# ---------------- COLUMNS ----------------
UNREAD_COLS = ["Title", "Author", "Cover URL", "Series", "Book Number"]
READ_COLS = ["Title", "Author", "Cover URL", "Series", "Book Number", "Rating"]
SAVINGS_COLS = ["Title", "Type", "Total Cost", "Saved", "Remaining"]
WRITTEN_COLS = ["Title", "Year Written"]

# ---------------- HELPERS ----------------
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            return df[columns]
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

def clean_text(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

def safe_num(val):
    try:
        return float(val)
    except:
        return 9999

# ---------------- BOOK FETCH ----------------
def fetch_book_data(title):
    # 1) Google Books first
    try:
        google_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}"
        response = requests.get(google_url, timeout=10)
        data = response.json()

        if "items" in data and len(data["items"]) > 0:
            book = data["items"][0]
            info = book.get("volumeInfo", {})

            found_title = info.get("title", title)

            authors = info.get("authors", [])
            author = authors[0] if len(authors) > 0 else "Unknown"

            image_links = info.get("imageLinks", {})
            cover_url = ""
            if "thumbnail" in image_links:
                cover_url = image_links["thumbnail"].replace("http://", "https://")
            elif "smallThumbnail" in image_links:
                cover_url = image_links["smallThumbnail"].replace("http://", "https://")

            return {
                "title": found_title,
                "author": author,
                "cover_url": cover_url
            }
    except:
        pass

    # 2) OpenLibrary fallback
    try:
        open_url = f"https://openlibrary.org/search.json?title={title}"
        response = requests.get(open_url, timeout=10)
        data = response.json()

        if "docs" in data and len(data["docs"]) > 0:
            book = data["docs"][0]
            found_title = book.get("title", title)

            author = "Unknown"
            if "author_name" in book and len(book["author_name"]) > 0:
                author = book["author_name"][0]

            cover_url = ""
            if "cover_i" in book:
                cover_url = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"

            return {
                "title": found_title,
                "author": author,
                "cover_url": cover_url
            }
    except:
        pass

    return {
        "title": title,
        "author": "Unknown",
        "cover_url": ""
    }

# ---------------- LOAD ALL DATA ----------------
unread_df = load_data(UNREAD_FILE, UNREAD_COLS)
read_df = load_data(READ_FILE, READ_COLS)
savings_df = load_data(SAVINGS_FILE, SAVINGS_COLS)
written_df = load_data(WRITTEN_FILE, WRITTEN_COLS)

# ---------------- STYLE ----------------
st.markdown("""
<style>
.big-title {
    font-size: 42px;
    font-weight: 700;
    color: #2f5d50;
}
.section-box {
    background-color: #fffdfd;
    padding: 14px;
    border-radius: 16px;
    border: 1px solid #f2d8e5;
    margin-bottom: 14px;
}
.small-note {
    color: #777;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- PAGE HEADER ----------------
st.markdown('<div class="big-title">K.K\'s Book App 💚🩷</div>', unsafe_allow_html=True)
st.write("Your books, your savings, and your own stories ✨")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📚 Unread Books", "✅ Read Books", "💰 Savings Tracker", "✍️ My Written Books"]
)

# =========================================================
# UNREAD BOOKS
# =========================================================
with tab1:
    st.subheader("Unread Books 📚")
    st.caption("Books you already own but haven’t read yet.")

    with st.expander("➕ Add unread book"):
        title = st.text_input("Book title", key="unread_title")

        is_series = st.checkbox("This book is part of a series", key="unread_series_check")
        series_name = ""
        book_no = ""

        if is_series:
            series_name = st.text_input("Series name", key="unread_series_name")
            book_no = st.text_input("Book number in series", key="unread_book_no")

        if st.button("Add to Unread", key="add_unread_btn"):
            if clean_text(title) != "":
                book = fetch_book_data(title)

                new_row = pd.DataFrame([{
                    "Title": book["title"],
                    "Author": book["author"],
                    "Cover URL": book["cover_url"],
                    "Series": series_name if is_series else "",
                    "Book Number": book_no if is_series else ""
                }])

                unread_df = pd.concat([unread_df, new_row], ignore_index=True)
                save_data(unread_df, UNREAD_FILE)
                st.success(f"{book['title']} added to unread books 💚")
                st.rerun()

    if len(unread_df) == 0:
        st.info("No unread books yet.")
    else:
        temp = unread_df.copy()
        temp["Series"] = temp["Series"].fillna("").astype(str)
        temp["Book Number"] = temp["Book Number"].fillna("").astype(str)

        series_books = temp[temp["Series"].str.strip() != ""]
        standalone_books = temp[temp["Series"].str.strip() == ""]

        # ----- SERIES BOOKS -----
        if len(series_books) > 0:
            st.markdown("## 📚 Series Books")
            grouped = series_books.groupby("Series", sort=True)

            for series_name, group in grouped:
                st.markdown(f"### 💚 {series_name}")
                group = group.copy()
                group["sort_num"] = group["Book Number"].apply(safe_num)
                group = group.sort_values(by=["sort_num", "Title"])

                for idx, row in group.iterrows():
                    st.markdown("---")
                    c1, c2 = st.columns([1, 3])

                    with c1:
                        cover = clean_text(row["Cover URL"])
                        if cover != "":
                            st.image(cover, width=140)
                        else:
                            st.caption("No cover found")

                    with c2:
                        st.markdown(f"### {row['Title']}")
                        st.write(f"**Author:** {row['Author']}")
                        st.write(f"**Series:** {row['Series']} | **Book:** {row['Book Number']}")

                        b1, b2 = st.columns(2)

                        with b1:
                            if st.button(f"Mark as Read - {row['Title']}", key=f"unread_to_read_{idx}"):
                                new_read = pd.DataFrame([{
                                    "Title": row["Title"],
                                    "Author": row["Author"],
                                    "Cover URL": row["Cover URL"],
                                    "Series": row["Series"],
                                    "Book Number": row["Book Number"],
                                    "Rating": ""
                                }])

                                read_df = pd.concat([read_df, new_read], ignore_index=True)
                                unread_df = unread_df.drop(idx).reset_index(drop=True)

                                save_data(unread_df, UNREAD_FILE)
                                save_data(read_df, READ_FILE)
                                st.success(f"{row['Title']} moved to Read Books 🩷")
                                st.rerun()

                        with b2:
                            if st.button(f"Delete unread - {row['Title']}", key=f"delete_unread_{idx}"):
                                unread_df = unread_df.drop(idx).reset_index(drop=True)
                                save_data(unread_df, UNREAD_FILE)
                                st.warning(f"{row['Title']} deleted")
                                st.rerun()

        # ----- STANDALONE BOOKS -----
        if len(standalone_books) > 0:
            st.markdown("## 🌸 Standalone Books")

            for idx, row in standalone_books.iterrows():
                st.markdown("---")
                c1, c2 = st.columns([1, 3])

                with c1:
                    cover = clean_text(row["Cover URL"])
                    if cover != "":
                        st.image(cover, width=140)
                    else:
                        st.caption("No cover found")

                with c2:
                    st.markdown(f"### {row['Title']}")
                    st.write(f"**Author:** {row['Author']}")

                    b1, b2 = st.columns(2)

                    with b1:
                        if st.button(f"Mark standalone as Read - {row['Title']}", key=f"standalone_to_read_{idx}"):
                            new_read = pd.DataFrame([{
                                "Title": row["Title"],
                                "Author": row["Author"],
                                "Cover URL": row["Cover URL"],
                                "Series": "",
                                "Book Number": "",
                                "Rating": ""
                            }])

                            read_df = pd.concat([read_df, new_read], ignore_index=True)
                            unread_df = unread_df.drop(idx).reset_index(drop=True)

                            save_data(unread_df, UNREAD_FILE)
                            save_data(read_df, READ_FILE)
                            st.success(f"{row['Title']} moved to Read Books 🩷")
                            st.rerun()

                    with b2:
                        if st.button(f"Delete standalone unread - {row['Title']}", key=f"delete_unread_standalone_{idx}"):
                            unread_df = unread_df.drop(idx).reset_index(drop=True)
                            save_data(unread_df, UNREAD_FILE)
                            st.warning(f"{row['Title']} deleted")
                            st.rerun()

# =========================================================
# READ BOOKS
# =========================================================
with tab2:
    st.subheader("Read Books ✅")
    st.caption("Books you’ve already finished.")

    with st.expander("➕ Add read book"):
        title = st.text_input("Book title", key="read_title")

        is_series = st.checkbox("This book is part of a series", key="read_series_check")
        series_name = ""
        book_no = ""

        if is_series:
            series_name = st.text_input("Series name", key="read_series_name")
            book_no = st.text_input("Book number in series", key="read_book_no")

        rating = st.selectbox(
            "Rating",
            ["", "1 ⭐", "2 ⭐", "3 ⭐", "4 ⭐", "5 ⭐"],
            key="read_rating"
        )

        if st.button("Add to Read", key="add_read_btn"):
            if clean_text(title) != "":
                book = fetch_book_data(title)

                new_row = pd.DataFrame([{
                    "Title": book["title"],
                    "Author": book["author"],
                    "Cover URL": book["cover_url"],
                    "Series": series_name if is_series else "",
                    "Book Number": book_no if is_series else "",
                    "Rating": rating
                }])

                read_df = pd.concat([read_df, new_row], ignore_index=True)
                save_data(read_df, READ_FILE)
                st.success(f"{book['title']} added to read books 🩷")
                st.rerun()

    if len(read_df) == 0:
        st.info("No read books yet.")
    else:
        temp = read_df.copy()
        temp["Series"] = temp["Series"].fillna("").astype(str)
        temp["Book Number"] = temp["Book Number"].fillna("").astype(str)

        series_books = temp[temp["Series"].str.strip() != ""]
        standalone_books = temp[temp["Series"].str.strip() == ""]

        # ----- SERIES -----
        if len(series_books) > 0:
            st.markdown("## 📖 Series Books")
            grouped = series_books.groupby("Series", sort=True)

            for series_name, group in grouped:
                st.markdown(f"### 🩷 {series_name}")
                group = group.copy()
                group["sort_num"] = group["Book Number"].apply(safe_num)
                group = group.sort_values(by=["sort_num", "Title"])

                for idx, row in group.iterrows():
                    st.markdown("---")
                    c1, c2 = st.columns([1, 3])

                    with c1:
                        cover = clean_text(row["Cover URL"])
                        if cover != "":
                            st.image(cover, width=140)
                        else:
                            st.caption("No cover found")

                    with c2:
                        st.markdown(f"### {row['Title']}")
                        st.write(f"**Author:** {row['Author']}")
                        st.write(f"**Series:** {row['Series']} | **Book:** {row['Book Number']}")
                        st.write(f"**Rating:** {row['Rating']}")

                        if st.button(f"Delete read - {row['Title']}", key=f"delete_read_{idx}"):
                            read_df = read_df.drop(idx).reset_index(drop=True)
                            save_data(read_df, READ_FILE)
                            st.warning(f"{row['Title']} deleted")
                            st.rerun()

        # ----- STANDALONE -----
        if len(standalone_books) > 0:
            st.markdown("## 🌸 Standalone Books")

            for idx, row in standalone_books.iterrows():
                st.markdown("---")
                c1, c2 = st.columns([1, 3])

                with c1:
                    cover = clean_text(row["Cover URL"])
                    if cover != "":
                        st.image(cover, width=140)
                    else:
                        st.caption("No cover found")

                with c2:
                    st.markdown(f"### {row['Title']}")
                    st.write(f"**Author:** {row['Author']}")
                    st.write(f"**Rating:** {row['Rating']}")

                    if st.button(f"Delete standalone read - {row['Title']}", key=f"delete_read_standalone_{idx}"):
                        read_df = read_df.drop(idx).reset_index(drop=True)
                        save_data(read_df, READ_FILE)
                        st.warning(f"{row['Title']} deleted")
                        st.rerun()

# =========================================================
# SAVINGS TRACKER
# =========================================================
with tab3:
    st.subheader("Savings Tracker 💰")
    st.caption("Track books or series you want to buy later.")

    unread_count = len(unread_df)
    if unread_count > 0:
        st.warning(f"You still have {unread_count} unread book(s) waiting 👀")

    with st.expander("➕ Add savings goal"):
        save_title = st.text_input("Book / series name", key="save_title")
        save_type = st.selectbox("Type", ["Book", "Series"], key="save_type")
        total_cost = st.number_input("Total cost", min_value=0.0, step=1.0, key="save_total")
        saved_amount = st.number_input("Saved so far", min_value=0.0, step=1.0, key="save_saved")

        if st.button("Add to Savings", key="add_savings_btn"):
            if clean_text(save_title) != "":
                remaining = max(total_cost - saved_amount, 0)

                new_row = pd.DataFrame([{
                    "Title": save_title,
                    "Type": save_type,
                    "Total Cost": total_cost,
                    "Saved": saved_amount,
                    "Remaining": remaining
                }])

                savings_df = pd.concat([savings_df, new_row], ignore_index=True)
                save_data(savings_df, SAVINGS_FILE)
                st.success(f"{save_title} added to savings 💰")
                st.rerun()

    if len(savings_df) == 0:
        st.info("No savings items yet.")
    else:
        total_cost_all = pd.to_numeric(savings_df["Total Cost"], errors="coerce").fillna(0).sum()
        total_saved_all = pd.to_numeric(savings_df["Saved"], errors="coerce").fillna(0).sum()
        total_remaining_all = pd.to_numeric(savings_df["Remaining"], errors="coerce").fillna(0).sum()

        st.markdown("### Overall Savings")
        st.write(f"**Total Cost:** ₹{total_cost_all}")
        st.write(f"**Saved:** ₹{total_saved_all}")
        st.write(f"**Remaining:** ₹{total_remaining_all}")

        st.markdown("---")

        for i, row in savings_df.iterrows():
            st.markdown(f"### {row['Title']}")
            st.write(f"**Type:** {row['Type']}")
            st.write(f"**Total Cost:** ₹{row['Total Cost']}")
            st.write(f"**Saved:** ₹{row['Saved']}")
            st.write(f"**Remaining:** ₹{row['Remaining']}")

            try:
                remaining_val = float(row["Remaining"])
            except:
                remaining_val = 0

            if remaining_val <= 0:
                st.success(f"Yayyy 💚🩷 You saved enough for {row['Title']}!")

            if st.button(f"Delete savings - {row['Title']}", key=f"delete_savings_{i}"):
                savings_df = savings_df.drop(i).reset_index(drop=True)
                save_data(savings_df, SAVINGS_FILE)
                st.warning(f"{row['Title']} deleted from savings")
                st.rerun()

# =========================================================
# MY WRITTEN BOOKS
# =========================================================
with tab4:
    st.subheader("My Written Books ✍️")
    st.caption("Your own books as K. K.")

    with st.expander("➕ Add written book"):
        my_title = st.text_input("Book title", key="my_written_title")
        my_year = st.text_input("Year written", key="my_written_year")

        if st.button("Save written book", key="save_written_btn"):
            if clean_text(my_title) != "":
                new_row = pd.DataFrame([{
                    "Title": my_title,
                    "Year Written": my_year
                }])

                written_df = pd.concat([written_df, new_row], ignore_index=True)
                save_data(written_df, WRITTEN_FILE)
                st.success(f"{my_title} added to your written books ✍️")
                st.rerun()

    if len(written_df) == 0:
        st.info("No written books added yet.")
    else:
        for i, row in written_df.iterrows():
            st.markdown("---")
            st.markdown(f"### {row['Title']}")
            st.write(f"**Year Written:** {row['Year Written']}")

            if st.button(f"Delete written - {row['Title']}", key=f"delete_written_{i}"):
                written_df = written_df.drop(i).reset_index(drop=True)
                save_data(written_df, WRITTEN_FILE)
                st.warning(f"{row['Title']} deleted from written books")
                st.rerun()