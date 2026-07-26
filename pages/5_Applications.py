import streamlit as st

from application_manager import (
    get_applications,
    delete_application,
    update_application_status,
    update_interview_date
)



# ==========================
# CONFIG
# ==========================

st.set_page_config(
    page_title="Application Tracker",
    page_icon="💼",
    layout="wide"
)



# ==========================
# STYLE
# ==========================

st.markdown(
"""
<style>


.stApp{

background:#070B14;

}



h1,h2,h3{

color:#F8FAFC;

}



.card{

background:#111827;

border:1px solid #263244;

border-radius:18px;

padding:18px;

margin-bottom:15px;

}



.company{

font-size:22px;

font-weight:800;

color:white;

}



.role{

font-size:16px;

color:#38BDF8;

font-weight:600;

}



.status{

font-size:13px;

background:#1E293B;

padding:6px 12px;

border-radius:20px;

display:inline-block;

}



.small{

color:#94A3B8;

font-size:13px;

}



/* RED DELETE BUTTON */

div[data-testid="stButton"] button{

border-radius:12px;

}



.delete-btn button{

background:#DC2626 !important;

color:white !important;

border:none !important;

}



.delete-btn button:hover{

background:#B91C1C !important;

}



</style>

""",
unsafe_allow_html=True
)





# ==========================
# HEADER
# ==========================


st.title(
"💼 Application Tracker"
)


st.caption(
"Manage your job applications, interviews and offers"
)


st.divider()





applications=get_applications()



if not applications:


    st.info(
        "No applications yet. Start applying!"
    )


    st.stop()





# ==========================
# SUMMARY
# ==========================


status_count={


"Applied":0,

"Interview":0,

"Offer":0,

"Rejected":0

}



for app in applications:


    status=app.get(
        "status",
        "Applied"
    )


    if status in status_count:

        status_count[status]+=1




c1,c2,c3,c4,c5=st.columns(5)



c1.metric(
"Total",
len(applications)
)


c2.metric(
"Applied",
status_count["Applied"]
)


c3.metric(
"Interview",
status_count["Interview"]
)


c4.metric(
"Offers",
status_count["Offer"]
)


c5.metric(
"Rejected",
status_count["Rejected"]
)



st.divider()





# ==========================
# KANBAN BOARD
# ==========================


columns=st.columns(4)



boards=[

("Applied","📨"),

("Interview","🎤"),

("Offer","🎉"),

("Rejected","❌")

]





for col,(status,icon) in zip(columns,boards):


    with col:


        st.subheader(
            f"{icon} {status}"
        )



        apps=[

            x for x in applications

            if x.get("status")==status

        ]



        if not apps:


            st.caption(
                "No applications"
            )




        for app in apps:



            # ==========================
            # CARD
            # ==========================


            st.markdown(

            f"""

            <div class="card">


            <div class="role">

            {app.get('role','Role')}

            </div>


            <div class="company">

            {app.get('company','Company')}

            </div>


            <br>


            <span class="status">

            {app.get('status')}

            </span>


            </div>


            """,

            unsafe_allow_html=True

            )




            # ==========================
            # STATUS BUTTON
            # ==========================


            with st.popover(
                "📌 Status"
            ):


                new_status=st.selectbox(

                    "Change Status",

                    [

                    "Applied",

                    "Interview",

                    "Offer",

                    "Rejected"

                    ],

                    index=[

                    "Applied",

                    "Interview",

                    "Offer",

                    "Rejected"

                    ].index(

                        app.get(
                            "status",
                            "Applied"
                        )

                    ),

                    key=f"status_{app['id']}"

                )



                if new_status != app["status"]:


                    update_application_status(

                        app["id"],

                        new_status

                    )


                    st.success(
                        "Status updated"
                    )


                    st.rerun()




                if new_status=="Interview":


                    date=st.date_input(

                        "Interview Date",

                        key=f"date_{app['id']}"

                    )



                    if st.button(

                        "Save Interview Date",

                        key=f"save_date_{app['id']}"

                    ):


                        update_interview_date(

                            app["id"],

                            str(date)

                        )


                        st.success(
                            "Interview date saved"
                        )


                        st.rerun()






            # ==========================
            # DELETE CONFIRMATION
            # ==========================


            st.markdown(
            '<div class="delete-btn">',
            unsafe_allow_html=True
            )


            if st.button(

                "🗑 Delete",

                key=f"delete_{app['id']}"

            ):


                st.session_state[
                    f"confirm_delete_{app['id']}"
                ]=True



            st.markdown(
            "</div>",
            unsafe_allow_html=True
            )




            if st.session_state.get(

                f"confirm_delete_{app['id']}",

                False

            ):



                st.warning(

                    "⚠️ Are you sure you want to delete this application?"

                )



                c1,c2=st.columns(2)



                with c1:


                    if st.button(

                        "Cancel",

                        key=f"cancel_{app['id']}"

                    ):


                        st.session_state[
                            f"confirm_delete_{app['id']}"
                        ]=False


                        st.rerun()



                with c2:


                    if st.button(

                        "Yes, Delete",

                        key=f"confirm_{app['id']}"

                    ):


                        delete_application(

                            app["id"]

                        )


                        st.success(
                            "Application deleted"
                        )


                        st.rerun()





            # ==========================
            # DETAILS
            # ==========================


            with st.expander(

                "📄 View Job Details"

            ):


                st.write(

                    app.get(

                        "job_description",

                        "No description"

                    )

                )



                if app.get(

                    "interview_date"

                ):


                    st.info(

                        f"🎤 Interview Date: {app['interview_date']}"

                    )