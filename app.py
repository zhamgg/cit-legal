import streamlit as st
import pandas as pd
from datetime import datetime
import re
import uuid

# Initialize session state
if 'email_chains' not in st.session_state:
    st.session_state.email_chains = []
if 'next_ref_number' not in st.session_state:
    st.session_state.next_ref_number = 1


def generate_reference_number():
    """Generate a reference number in format: GG-LEGAL-YYYY-NNNN"""
    year = datetime.now().year
    ref_num = f"GG-LEGAL-{year}-{st.session_state.next_ref_number:04d}"
    st.session_state.next_ref_number += 1
    return ref_num


def extract_reference_from_subject(subject):
    """Extract reference number from subject line"""
    pattern = r'GG-LEGAL-\d{4}-\d{4}'
    match = re.search(pattern, subject)
    return match.group() if match else None


def add_email_to_chain(sender, recipient, subject, body, ref_number=None):
    """Add an email to the chain"""
    # If no reference number provided, check if subject contains one
    if not ref_number:
        ref_number = extract_reference_from_subject(subject)

    # If still no reference number, generate a new one
    if not ref_number:
        ref_number = generate_reference_number()

    # Ensure reference number is in subject line
    if ref_number not in subject:
        if subject.startswith("RE:"):
            subject = f"RE: [{ref_number}] {subject[3:].strip()}"
        else:
            subject = f"[{ref_number}] {subject}"

    email = {
        'id': str(uuid.uuid4())[:8],
        'timestamp': datetime.now(),
        'sender': sender,
        'recipient': recipient,
        'subject': subject,
        'body': body,
        'reference_number': ref_number,
        'thread_position': len([e for e in st.session_state.email_chains if e['reference_number'] == ref_number]) + 1
    }

    st.session_state.email_chains.append(email)
    return email


def get_emails_by_reference(ref_number):
    """Get all emails with a specific reference number"""
    return [e for e in st.session_state.email_chains if e['reference_number'] == ref_number]


def get_unique_references():
    """Get all unique reference numbers"""
    return list(set([e['reference_number'] for e in st.session_state.email_chains]))


# Streamlit UI
st.title("📧 Email Reference Number System")
st.markdown("*POC for Great Gray CIT Legal Team*")

# Sidebar for controls
st.sidebar.header("📊 System Stats")
st.sidebar.metric("Total Emails", len(st.session_state.email_chains))
st.sidebar.metric("Active Threads", len(get_unique_references()))
st.sidebar.markdown("**Next Reference #**")
st.sidebar.markdown(f'<small>{f"GG-LEGAL-{datetime.now().year}-{st.session_state.next_ref_number:04d}"}</small>', unsafe_allow_html=True)

if st.sidebar.button("🗑️ Clear All Data"):
    st.session_state.email_chains = []
    st.session_state.next_ref_number = 1
    st.success("✅ All data cleared!")

# Main tabs
tab1, tab2, tab3 = st.tabs(["📝 Compose Email", "📨 Email Threads", "🔍 Search by Reference"])

with tab1:
    st.header("Compose New Email")

    col1, col2 = st.columns(2)
    with col1:
        sender = st.text_input("From:", value="citlegalsupport@greatgray.com")
        recipient = st.text_input("To:", value="client@company.com")

    with col2:
        is_reply = st.checkbox("This is a reply to existing thread")
        if is_reply:
            existing_refs = get_unique_references()
            if existing_refs:
                selected_ref = st.selectbox("Select Reference Number:", existing_refs)
            else:
                st.warning("No existing threads to reply to")
                selected_ref = None
        else:
            selected_ref = None

    subject = st.text_input("Subject:", value="Legal Service Request")
    body = st.text_area("Email Body:",
                        value="""Thank you for contacting the Great Gray CIT Support Legal Mailbox.

As a team, we strive to process and provide legal services within a minimum of five (5) business days.
In some cases, time sensitive matters may receive a higher priority of service.
As a result, certain legal service requests may take more than five (5) business days.
Additionally, our processing timeline will vary depending on the nature of the request and the availability of information/documents necessary for review.

A member of Great Gray Legal Team will contact you soon regarding this request, but in the meantime, if you need to contact us with questions or provide additional information regarding this matter, *please reference the number in the subject line on all correspondence.*

We look forward to servicing your request.

The Great Gray CIT Legal Team""",
                        height=200)

    if st.button("📤 Send Email"):
        ref_to_use = selected_ref if is_reply and selected_ref else None
        email = add_email_to_chain(sender, recipient, subject, body, ref_to_use)
        st.success(f"✅ Email sent with reference number: **{email['reference_number']}**")
        st.info(f"📋 Final subject line: **{email['subject']}**")

with tab2:
    st.header("Email Threads")

    if not st.session_state.email_chains:
        st.info("No emails yet. Compose your first email in the 'Compose Email' tab.")
    else:
        # Group emails by reference number
        references = get_unique_references()

        for ref in sorted(references):
            with st.expander(f"🔗 Thread: {ref} ({len(get_emails_by_reference(ref))} emails)"):
                thread_emails = sorted(get_emails_by_reference(ref),
                                       key=lambda x: x['timestamp'])

                for i, email in enumerate(thread_emails):
                    st.markdown(f"**Email #{i + 1}** - {email['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"**From:** {email['sender']}")
                    st.markdown(f"**To:** {email['recipient']}")
                    st.markdown(f"**Subject:** {email['subject']}")
                    st.markdown(f"**Body:**")
                    st.text_area("", value=email['body'], height=100,
                                 key=f"body_{email['id']}", disabled=True)
                    st.markdown("---")

with tab3:
    st.header("Search by Reference Number")

    if get_unique_references():
        search_ref = st.selectbox("Select Reference Number to Search:",
                                  [""] + sorted(get_unique_references()))

        if search_ref:
            emails = get_emails_by_reference(search_ref)
            st.success(f"Found {len(emails)} emails with reference {search_ref}")

            # Display search results
            for i, email in enumerate(sorted(emails, key=lambda x: x['timestamp'])):
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**#{i + 1}:** {email['sender']} → {email['recipient']}")
                    with col2:
                        st.write(f"**Subject:** {email['subject']}")
                    with col3:
                        st.write(f"**Time:** {email['timestamp'].strftime('%H:%M:%S')}")

                    if st.button(f"View Email #{i + 1}", key=f"view_{email['id']}"):
                        st.text_area("Email Body:", value=email['body'],
                                     height=150, key=f"search_body_{email['id']}")
    else:
        st.info("No email threads available to search.")

# Footer
st.markdown("---")
st.markdown("""
### 💡 How This System Works:

1. **Automatic Reference Numbers**: Each new email thread gets a unique reference number (GG-LEGAL-YYYY-NNNN format)
2. **Subject Line Integration**: Reference numbers are automatically added to subject lines
3. **Thread Tracking**: All replies with the same reference number are grouped together
4. **Easy Search**: Find any email by its reference number
5. **Sequential Numbering**: Each reply in a thread can be easily identified by position

### Benefits:
- ✅ No more scrolling through dozens of emails
- ✅ Quick reference for clients and team members  
- ✅ Professional tracking system
- ✅ Easy handoffs between team members
- ✅ Audit trail for legal matters
""")
