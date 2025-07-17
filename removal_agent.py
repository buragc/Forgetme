import os
from playwright.sync_api import sync_playwright
from langgraph.graph import StateGraph
from typing import Optional, List
from datetime import datetime
import sqlite3
from dotenv import load_dotenv
import anthropic
from bs4 import BeautifulSoup
from twocaptcha import TwoCaptcha


# Load environment variables from .env
load_dotenv()

# Actual Anthropic API call

def ask_anthropic(question: str, context: str) -> str:
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("[Anthropic] API key not set!")
        return ""
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"You are an expert at navigating websites to find data removal or opt-out options. "
        f"Given the following web page HTML, answer the following question as concisely as possible.\n"
        f"\nHTML:\n{context}\n\nQuestion: {question}\n"
        f"If there is a direct link or button for data removal, opt-out, or privacy request, provide the exact visible text or selector. "
        f"If not, suggest the most likely FAQ, Help, Privacy, or Contact link to follow. "
        f"If nothing is found, say 'No removal path found.'"
    )
    print(f"[Anthropic] Sending prompt to Claude: {question}")
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=256,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.content[0].text.strip() if hasattr(response, 'content') and response.content else str(response)
    print(f"[Anthropic] Response: {answer}")
    return answer

def extract_removal_candidates(html):
    """
    Extracts candidate elements (links, buttons, forms) that may be related to data removal.
    Returns a list of dicts with text, type, and a simple selector.
    """
    soup = BeautifulSoup(html, 'html.parser')
    candidates = []
    keywords = ['remove', 'removal', 'do not use', 'opt out', 'delete', 'privacy', 'do not sell', 'unsubscribe']

    # Find links and buttons
    for tag in soup.find_all(['a', 'button', 'input']):
        text = (tag.get_text() or '').strip() + ' ' + (tag.get('value') or '')
        text = text.strip()
        if any(kw in text.lower() for kw in keywords):
            selector = ''
            if tag.name == 'a' and tag.get('href'):
                selector = f"a[href='{tag.get('href')}']"
            elif tag.name == 'button' and tag.get('id'):
                selector = f"button#{tag.get('id')}"
            elif tag.name == 'input' and tag.get('name'):
                selector = f"input[name='{tag.get('name')}']"
            else:
                selector = str(tag)[:80]  # fallback: truncated HTML
            candidates.append({
                'text': text,
                'type': tag.name,
                'selector': selector
            })

    # Find forms with relevant keywords in labels/placeholders
    for form in soup.find_all('form'):
        form_text = form.get_text(separator=' ', strip=True)
        if any(kw in form_text.lower() for kw in keywords):
            candidates.append({
                'text': form_text[:100],
                'type': 'form',
                'selector': 'form'
            })

    return candidates

def build_claude_removal_prompt(candidates):
    """
    Build a minimal prompt for Claude given a list of candidate elements.
    """
    if not candidates:
        return "No removal-related elements found on this page."
    prompt = "Here are the candidate elements for data removal on this page:\n"
    for i, c in enumerate(candidates, 1):
        prompt += f"{i}. Text: \"{c['text']}\", Type: {c['type']}, Selector: {c['selector']}\n"
    prompt += "Which one is most likely for data removal? Reply with the number."
    return prompt

# Placeholder for sending email (to be implemented)
def send_email(to_email: str, subject: str, body: str):
    print(f"[Email] Sending email to: {to_email} | Subject: {subject} | Body: {body}")
    # TODO: Integrate with your email sending logic/component
    print(f"[TOOL CALL] send_email(to={to_email}, subject={subject}, body={body})")

# User data for form/email
USER_DATA = {
    "name": "Burag Cetinkaya",
    "email": "f3935235+peoplebyname@gmail.com",
    "phone": "516-342-0919",
    "subject": "Remove my info",
    "message": "Please remove me from your list.",
    "alt_email": "buragc@gmail.com"
}

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

DB_NAME = 'brokers.db'

def save_screenshot(page, step_name, broker_name=None):
    from datetime import datetime
    import re
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # Sanitize broker name for file path
    if broker_name:
        safe_broker = re.sub(r'[^a-zA-Z0-9_-]', '_', broker_name)[:40]
        filename = f"{SCREENSHOT_DIR}/{safe_broker}_{step_name}_{timestamp}.png"
    else:
        filename = f"{SCREENSHOT_DIR}/{step_name}_{timestamp}.png"
    page.screenshot(path=filename, full_page=True)
    print(f"[Screenshot] Saved: {filename}")
    return filename

# --- Agent Steps ---
def step_navigate(state: dict):
    print(f"[Step] Navigating to {state['url']}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(state['url'])
        broker_name = state.get('broker_name')
        screenshot_path = save_screenshot(page, "navigate", broker_name)
        state['screenshots'].append(screenshot_path)
        state['html'] = page.content()
        browser.close()
    print(f"[Step] Navigation complete.")
    return state

def step_find_removal_path(state: dict):
    print("[Step] Finding removal path using local extraction and Claude reasoning...")
    candidates = extract_removal_candidates(state['html'])
    prompt = build_claude_removal_prompt(candidates)
    print("[Step] Claude prompt:\n", prompt)
    suggestion = ask_anthropic(prompt, "")  # Only send the prompt, not the full HTML
    state['steps'].append(f"Anthropic suggestion: {suggestion}")
    import re
    match = re.search(r'(opt[- ]?out|remove|do not sell|privacy|delete)', state['html'], re.I)
    if match:
        state['status'] = 'removal_path_found'
        state['steps'].append(f"Found likely removal path: {match.group(0)}")
        print(f"[Step] Found likely removal path: {match.group(0)}")
    else:
        state['status'] = 'manual_intervention_required'
        state['result'] = 'Could not find removal path.'
        print("[Step] Could not find removal path. Manual intervention required.")
    # Screenshot logic (if needed)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(state['url'])
        broker_name = state.get('broker_name')
        screenshot_path = save_screenshot(page, "find_removal_path", broker_name)
        state['screenshots'].append(screenshot_path)
        browser.close()
    return state

def step_find_form_or_email(state: dict):
    print("[Step] Looking for removal form or email address...")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(state['html'], 'html.parser')
    form = soup.find('form')
    if form:
        state['status'] = 'form_found'
        state['steps'].append('Found removal form.')
        state['form'] = form
        print("[Step] Found removal form.")
    else:
        import re
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', state['html'])
        if emails:
            state['found_email'] = emails[0]
            state['status'] = 'email_found'
            state['steps'].append(f'Found email address: {emails[0]}')
            print(f"[Step] Found email address: {emails[0]}")
        else:
            state['status'] = 'manual_intervention_required'
            state['result'] = 'No form or email found.'
            print("[Step] No form or email found. Manual intervention required.")
    if 'page' in state and state['page']:
        broker_name = state.get('broker_name')
        screenshot_path = save_screenshot(state['page'], "find_form_or_email", broker_name)
        state['screenshots'].append(screenshot_path)
    return state

def step_submit_form(state: dict):
    print("[Step] Submitting removal form with Playwright...")
    from bs4 import BeautifulSoup
    import re
    import requests
    from twocaptcha import TwoCaptcha
    import tempfile
    import shutil

    # Re-parse the HTML to find the form and its fields
    soup = BeautifulSoup(state['html'], 'html.parser')
    form = soup.find('form')
    if not form:
        state['status'] = 'manual_intervention_required'
        state['result'] = 'No form found on page for submission.'
        print("[Step] No form found. Manual intervention required.")
        return state

    # Extract form action and method
    form_action = form.get('action', state['url'])
    form_method = form.get('method', 'post').lower()

    # Map input names to USER_DATA keys (simple heuristic)
    input_map = {
        'name': USER_DATA['name'],
        'email': USER_DATA['email'],
        'phone': USER_DATA['phone'],
        'subject': USER_DATA['subject'],
        'message': USER_DATA['message'],
    }

    # Find all input fields
    inputs = form.find_all(['input', 'textarea'])
    field_values = {}
    for inp in inputs:
        name = inp.get('name')
        if not name:
            continue
        # Try to match input name to USER_DATA keys
        for key in input_map:
            if key in name.lower():
                field_values[name] = input_map[key]
                break

    # --- Captcha Detection ---
    captcha_type = None
    captcha_data = {}
    # reCAPTCHA v2/v3
    recaptcha_div = soup.find('div', class_=re.compile(r'g-recaptcha'))
    recaptcha_script = soup.find('script', src=re.compile(r'recaptcha\/api\.js'))
    if recaptcha_div or recaptcha_script:
        sitekey = None
        if recaptcha_div and recaptcha_div.has_attr('data-sitekey'):
            sitekey = recaptcha_div['data-sitekey']
        else:
            # Try to find sitekey in any element
            sitekey_tag = soup.find(attrs={'data-sitekey': True})
            if sitekey_tag:
                sitekey = sitekey_tag['data-sitekey']
        if sitekey:
            # Check for v3 by presence of 'grecaptcha.execute' or version param
            if soup.find('script', string=re.compile(r'grecaptcha\.execute')) or 'v3' in str(recaptcha_script):
                captcha_type = 'recaptcha_v3'
            else:
                captcha_type = 'recaptcha_v2'
            captcha_data['sitekey'] = sitekey
    # FunCaptcha
    elif soup.find('script', src=re.compile(r'funcaptcha\.com')):
        captcha_type = 'funcaptcha'
    # GeeTest
    elif soup.find('script', src=re.compile(r'geetest\.com')):
        captcha_type = 'geetest'
    # KeyCaptcha
    elif soup.find('script', src=re.compile(r'keycaptcha\.com')):
        captcha_type = 'keycaptcha'
    # Capy
    elif soup.find('script', src=re.compile(r'api\.capy\.me')):
        captcha_type = 'capy'
    # Grid/Canvas/ClickCaptcha/Rotate (look for canvas or keywords)
    elif soup.find('canvas') or soup.find(string=re.compile(r'grid|canvas|click captcha|rotate', re.I)):
        captcha_type = 'canvas_like'
    # Normal Captcha (image)
    else:
        captcha_img = None
        for img in soup.find_all('img'):
            if 'captcha' in (img.get('src', '') + img.get('alt', '')).lower():
                captcha_img = img
                break
        if captcha_img:
            captcha_type = 'normal'
            captcha_data['img_src'] = captcha_img.get('src')
    # Text Captcha (look for question near input)
    if not captcha_type:
        for label in soup.find_all(['label', 'span', 'div', 'p']):
            if re.search(r'(type the text|enter the answer|what day|solve|question)', label.get_text(), re.I):
                captcha_type = 'text'
                captcha_data['question'] = label.get_text(strip=True)
                break

    print(f"[Captcha] Detected type: {captcha_type}")
    state['steps'].append(f"Detected captcha type: {captcha_type}")

    # --- Captcha Solving ---
    captcha_solution = None
    solver = None
    try:
        solver = TwoCaptcha(os.getenv('TWOCAPTCHA_API_KEY'))
    except Exception as e:
        print(f"[Captcha] Could not instantiate TwoCaptcha solver: {e}")
        state['steps'].append(f"Could not instantiate TwoCaptcha solver: {e}")

    if solver and captcha_type:
        try:
            if captcha_type == 'recaptcha_v2':
                result = solver.recaptcha(sitekey=captcha_data['sitekey'], url=state['url'])
                captcha_solution = result['code']
            elif captcha_type == 'recaptcha_v3':
                result = solver.recaptcha(sitekey=captcha_data['sitekey'], url=state['url'], version='v3')
                captcha_solution = result['code']
            elif captcha_type == 'normal':
                # Download the image
                img_url = captcha_data['img_src']
                if not img_url.startswith('http'):
                    # Make relative URLs absolute
                    from urllib.parse import urljoin
                    img_url = urljoin(state['url'], img_url)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    resp = requests.get(img_url, stream=True)
                    if resp.status_code == 200:
                        shutil.copyfileobj(resp.raw, tmp)
                        tmp_path = tmp.name
                        result = solver.normal(tmp_path)
                        captcha_solution = result['code']
                        os.unlink(tmp_path)
            elif captcha_type == 'text':
                result = solver.text(captcha_data['question'])
                captcha_solution = result['code']
            else:
                state['steps'].append(f"Captcha type {captcha_type} detected but not implemented for solving.")
            if captcha_solution:
                print(f"[Captcha] Solved: {captcha_solution}")
                state['steps'].append(f"Captcha solved: {captcha_solution}")
            else:
                print(f"[Captcha] Could not solve captcha of type {captcha_type}")
                state['steps'].append(f"Could not solve captcha of type {captcha_type}")
        except Exception as e:
            print(f"[Captcha] Error solving captcha: {e}")
            state['steps'].append(f"Error solving captcha: {e}")

    # Use Playwright to fill and submit the form
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(state['url'])

        # Fill the fields
        for name, value in field_values.items():
            try:
                selector = f'[name="{name}"]'
                page.fill(selector, value)
                print(f"[Step] Filled {name} with {value}")
            except Exception as e:
                print(f"[Step] Could not fill {name}: {e}")

        # Inject captcha solution if available
        if captcha_solution:
            try:
                if captcha_type in ['recaptcha_v2', 'recaptcha_v3']:
                    # Set g-recaptcha-response value
                    page.evaluate(
                        f"""document.querySelector('textarea[name="g-recaptcha-response"]') && 
                        (document.querySelector('textarea[name="g-recaptcha-response"]').value = "{captcha_solution}")"""
                    )
                elif captcha_type == 'normal' or captcha_type == 'text':
                    # Try to find the input for captcha
                    for inp in form.find_all('input'):
                        if 'captcha' in (inp.get('name', '') + inp.get('id', '')).lower():
                            selector = f'[name="{inp.get("name")}"]' if inp.get('name') else f'#{inp.get("id")}'
                            page.fill(selector, captcha_solution)
                            break
                # Other types can be added here
                print(f"[Captcha] Injected solution for {captcha_type}")
                state['steps'].append(f"Injected captcha solution for {captcha_type}")
            except Exception as e:
                print(f"[Captcha] Could not inject captcha solution: {e}")
                state['steps'].append(f"Could not inject captcha solution: {e}")

        # Try to click the submit button
        try:
            submit_btn = form.find('button', {'type': 'submit'})
            if not submit_btn:
                # Try to find input[type=submit]
                submit_btn = form.find('input', {'type': 'submit'})
            if submit_btn and submit_btn.get('name'):
                selector = f'[name="{submit_btn.get("name")}"]'
                page.click(selector)
            else:
                # Fallback: submit the first button or input[type=submit]
                page.click('form button, form input[type=submit]')
            print("[Step] Submitted the form.")
        except Exception as e:
            print(f"[Step] Could not submit the form by clicking: {e}")
            # As a fallback, try to submit the form via JS
            try:
                page.eval_on_selector('form', 'form => form.submit()')
                print("[Step] Submitted the form via JS.")
            except Exception as e2:
                print(f"[Step] Could not submit the form via JS: {e2}")

        # Take a screenshot after submission
        broker_name = state.get('broker_name')
        screenshot_path = save_screenshot(page, "submit_form", broker_name)
        state['screenshots'].append(screenshot_path)
        state['status'] = 'form_submitted'
        state['result'] = 'Form submitted'
        state['steps'].append('Submitted removal form.')
        browser.close()

    if 'broker_id' in state and state['broker_id'] is not None:
        update_broker_submission(state['broker_id'])
        print(f"[DB] Updated brokerID {state['broker_id']} with removalState 'Requested' and current submissionDate.")
    print("[Step] Form submission complete.")
    return state

def step_send_email(state: dict):
    print("[Step] Sending removal request email...")
    send_email(
        to_email=state['found_email'],
        subject=USER_DATA['subject'],
        body=f"Name: {USER_DATA['name']}\nEmail: {USER_DATA['email']}\nPhone: {USER_DATA['phone']}\nMessage: {USER_DATA['message']}"
    )
    state['status'] = 'email_sent'
    state['result'] = f'Email sent to {state['found_email']}'
    state['steps'].append(f'Sent removal email to {state['found_email']}.')
    if 'page' in state and state['page']:
        broker_name = state.get('broker_name')
        screenshot_path = save_screenshot(state['page'], "send_email", broker_name)
        state['screenshots'].append(screenshot_path)
    print("[Step] Email send complete.")
    return state

# --- Database Helpers ---
def get_brokers_to_process():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT brokerID, brokerName, brokerURL FROM brokers WHERE removalState NOT IN ('Requested', 'Removed')")
    rows = c.fetchall()
    conn.close()
    print(f"[DB] Found {len(rows)} broker(s) to process.")
    return rows

def update_broker_submission(broker_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("UPDATE brokers SET removalState = ?, submissionDate = ? WHERE brokerID = ?", ('Requested', now, broker_id))
    conn.commit()
    conn.close()
    print(f"[DB] BrokerID {broker_id} updated: removalState='Requested', submissionDate={now}")

def reset_broker_submission(broker_id):
    """Reset a broker's removalState to 'Not Requested' and submissionDate to NULL."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE brokers SET removalState = ?, submissionDate = NULL WHERE brokerID = ?", ('Not Requested', broker_id))
    conn.commit()
    conn.close()
    print(f"[DB] BrokerID {broker_id} reset: removalState='Not Requested', submissionDate=NULL")
# Usage example:
# reset_broker_submission(1)

# --- LangGraph Orchestration ---
graph = StateGraph(dict)

graph.add_node('navigate', step_navigate)
graph.add_node('find_removal_path', step_find_removal_path)
graph.add_node('find_form_or_email', step_find_form_or_email)
graph.add_node('submit_form', step_submit_form)
graph.add_node('send_email', step_send_email)

def conditional_find_form_or_email(state: dict):
    if state['status'] == 'form_found':
        return 'submit_form'
    elif state['status'] == 'email_found':
        return 'send_email'
    else:
        return None

graph.add_edge('navigate', 'find_removal_path')
graph.add_edge('find_removal_path', 'find_form_or_email')
graph.add_conditional_edges('find_form_or_email', conditional_find_form_or_email)
# submit_form and send_email are terminal nodes

graph.set_entry_point('navigate')

graph_app = graph.compile()

def run_agent(url: str, broker_id: int = None, broker_name: str = None):
    print(f"[Agent] Starting removal process for: {url} (brokerID={broker_id})")
    state = {
        "url": url,
        "broker_id": broker_id,
        "broker_name": broker_name,
        "status": "initialized",
        "steps": [],
        "result": None,
        "found_email": None,
        "screenshots": [],
        # add any other fields your graph expects
    }
    state = graph_app.invoke(state)
    print('[Agent] Steps:')
    for step in state.get('steps', []):
        print('  -', step)
    print('[Agent] Result:', state.get('result'))
    print('[Agent] Screenshots:')
    for shot in state.get('screenshots', []):
        print('  -', shot)
    print('[Agent] Finished processing.')
    return state

if __name__ == '__main__':
    brokers = get_brokers_to_process()
    for brokerID, brokerName, brokerURL in brokers:
        print(f"\n[Main] Processing broker: {brokerName} ({brokerURL})")
        run_agent(brokerURL, brokerID, brokerName)
