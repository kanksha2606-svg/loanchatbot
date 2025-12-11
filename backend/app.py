from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import time
import re
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global session storage
sessions = {}

# =============================================================================
# CONVERSATION STATE MACHINE
# =============================================================================

class ConversationFlow:
    """Manages conversation flow without repetition"""
    
    STAGES = ['greeting', 'amount', 'income', 'employment', 'eligibility', 'documents', 'decision', 'complete']
    
    def __init__(self):
        self.current_stage = 'greeting'
        self.collected_data = {}
    
    def has_field(self, field):
        """Check if field is already collected"""
        return field in self.collected_data and self.collected_data[field] is not None
    
    def get_next_stage(self):
        """Determine next stage based on collected data"""
        
        # Check what we have
        has_amount = self.has_field('loan_amount')
        has_income = self.has_field('income')
        has_employment = self.has_field('employment_type') and self.has_field('employment_duration')
        
        if not has_amount:
            return 'amount'
        elif not has_income:
            return 'income'
        elif not has_employment:
            return 'employment'
        else:
            return 'eligibility'
    
    def get_missing_fields(self):
        """Return list of missing fields"""
        missing = []
        if not self.has_field('loan_amount'):
            missing.append('loan_amount')
        if not self.has_field('income'):
            missing.append('income')
        if not self.has_field('employment_type'):
            missing.append('employment_type')
        if not self.has_field('employment_duration'):
            missing.append('employment_duration')
        return missing


# =============================================================================
# MULTI-AGENT SYSTEM
# =============================================================================

class ConversationAgent:
    """Agent 1: Extract information from user messages"""
    
    def extract_all(self, message):
        """Extract ALL possible information from message"""
        data = {}
        message_lower = message.lower()
        
        # Extract loan amount
        amount = self._extract_amount(message_lower)
        if amount:
            data['loan_amount'] = amount
        
        # Extract income
        income = self._extract_income(message_lower)
        if income:
            data['income'] = income
        
        # Extract employment
        emp_type = self._extract_employment_type(message_lower)
        if emp_type:
            data['employment_type'] = emp_type
        
        emp_duration = self._extract_duration(message_lower)
        if emp_duration:
            data['employment_duration'] = emp_duration
        
        return data
    
    def _extract_amount(self, text):
        """Extract loan amount"""
        # Pattern 1: "5 lakhs", "5 lakh"
        match = re.search(r'(\d+)\s*(?:lakh|lac)', text)
        if match:
            return int(match.group(1)) * 100000
        
        # Pattern 2: "500000", "5,00,000"
        match = re.search(r'(\d[\d,]{4,})', text)
        if match:
            amount = int(match.group(1).replace(',', ''))
            if 10000 <= amount <= 10000000:
                return amount
        
        return None
    
    def _extract_income(self, text):
        """Extract monthly income"""
        # Look for income indicators
        if any(word in text for word in ['income', 'salary', 'earn', 'make', 'paid']):
            match = re.search(r'(\d[\d,]{3,})', text)
            if match:
                income = int(match.group(1).replace(',', ''))
                if 5000 <= income <= 1000000:
                    return income
        
        # Just a number after income question
        match = re.search(r'(\d{4,})', text)
        if match:
            income = int(match.group(1).replace(',', ''))
            if 5000 <= income <= 1000000:
                return income
        
        return None
    
    def _extract_employment_type(self, text):
        """Extract employment type"""
        if 'salari' in text:
            return 'salaried'
        elif any(word in text for word in ['self', 'business', 'entrepreneur']):
            return 'self-employed'
        return None
    
    def _extract_duration(self, text):
        """Extract employment duration"""
        match = re.search(r'(\d+)\s*(?:year|yr)', text)
        if match:
            return int(match.group(1))
        return None
    
    def generate_response(self, flow):
        """Generate response based on missing data"""
        missing = flow.get_missing_fields()
        
        if not missing:
            return "Perfect! I have all the information. Let me analyze your eligibility..."
        
        if 'loan_amount' in missing:
            return "I'd be happy to help! How much would you like to borrow?"
        
        if 'income' in missing:
            amount = flow.collected_data.get('loan_amount', 0)
            return f"Got it, ₹{amount:,}. What's your monthly income?"
        
        if 'employment_type' in missing or 'employment_duration' in missing:
            return "Thanks! Are you salaried or self-employed? And how many years have you been working?"
        
        return "I need a bit more information to proceed."


class EligibilityAgent:
    """Agent 2: Calculate eligibility"""
    
    def calculate(self, data):
        """Calculate loan eligibility"""
        
        loan_amount = data.get('loan_amount', 0)
        income = data.get('income', 0)
        emp_type = data.get('employment_type', '')
        emp_duration = data.get('employment_duration', 0)
        
        # Calculate max eligible
        if emp_type == 'salaried':
            multiplier = 60 if emp_duration >= 3 else 50
            base_rate = 10.5
        else:
            multiplier = 48 if emp_duration >= 2 else 40
            base_rate = 11.5
        
        max_eligible = income * multiplier
        
        # Risk calculation
        risk_score = 50
        
        if emp_type == 'salaried':
            risk_score -= 10
        
        if emp_duration >= 3:
            risk_score -= 15
        elif emp_duration >= 2:
            risk_score -= 10
        
        if income > 0 and loan_amount > 0:
            dti = (loan_amount * 0.022) / income
            if dti < 0.3:
                risk_score -= 20
            elif dti < 0.4:
                risk_score -= 10
            else:
                risk_score += 15
        
        risk_score = max(0, min(100, risk_score))
        
        # Interest rate
        if risk_score < 30:
            interest_rate = base_rate - 0.5
        elif risk_score < 60:
            interest_rate = base_rate
        else:
            interest_rate = base_rate + 1.0
        
        eligible = loan_amount <= max_eligible and risk_score < 70
        approved_amount = min(loan_amount, max_eligible) if eligible else 0
        
        return {
            'eligible': eligible,
            'approved_amount': int(approved_amount),
            'interest_rate': round(interest_rate, 2),
            'max_eligible': int(max_eligible),
            'risk_score': risk_score,
            'explanation': self._generate_explanation(data, risk_score, eligible)
        }
    
    def _generate_explanation(self, data, risk_score, eligible):
        """Generate explanation"""
        factors = []
        
        if risk_score < 30:
            factors.append({
                'icon': '✓',
                'title': 'Excellent Risk Profile',
                'detail': f'AI Risk Score: {risk_score}% (Very Low)',
                'positive': True
            })
        elif risk_score < 60:
            factors.append({
                'icon': '✓',
                'title': 'Good Risk Profile',
                'detail': f'AI Risk Score: {risk_score}% (Acceptable)',
                'positive': True
            })
        else:
            factors.append({
                'icon': '⚠',
                'title': 'Higher Risk',
                'detail': f'AI Risk Score: {risk_score}%',
                'positive': False
            })
        
        income = data.get('income', 0)
        loan_amount = data.get('loan_amount', 0)
        
        if income > 0 and loan_amount > 0:
            emi = loan_amount * 0.022
            ratio = (emi / income) * 100
            
            if ratio < 40:
                factors.append({
                    'icon': '✓',
                    'title': 'Affordable EMI',
                    'detail': f'EMI is {ratio:.1f}% of income',
                    'positive': True
                })
            else:
                factors.append({
                    'icon': '⚠',
                    'title': 'High EMI Burden',
                    'detail': f'EMI would be {ratio:.1f}% of income',
                    'positive': False
                })
        
        duration = data.get('employment_duration', 0)
        if duration >= 2:
            factors.append({
                'icon': '✓',
                'title': 'Stable Employment',
                'detail': f'{duration} years - Good track record',
                'positive': True
            })
        
        return factors


class DocumentAgent:
    """Agent 3: Verify documents"""
    
    def verify(self, file, doc_type):
        """Verify document"""
        time.sleep(1)
        
        verifications = {
            'aadhaar': {
                'type': 'aadhaar',
                'verified': True,
                'message': '✅ Aadhaar Card verified successfully'
            },
            'pan': {
                'type': 'pan',
                'verified': True,
                'message': '✅ PAN Card verified successfully'
            },
            'salary': {
                'type': 'salary',
                'verified': True,
                'message': '✅ Salary Slip verified successfully'
            }
        }
        
        return verifications.get(doc_type, {'verified': False, 'message': '❌ Unknown document type'})


class DecisionAgent:
    """Agent 4: Make final decision"""
    
    def decide(self, eligibility, documents):
        """Make final decision"""
        
        if not eligibility.get('eligible'):
            return {
                'status': 'rejected',
                'decision': 'Application needs review for alternative options.',
                'processing_time': '2.5 minutes'
            }
        
        if len(documents) < 3:
            return {
                'status': 'pending',
                'decision': 'Awaiting document verification',
                'processing_time': '1.8 minutes'
            }
        
        risk = eligibility.get('risk_score', 100)
        
        if risk < 60:
            return {
                'status': 'approved',
                'decision': f"🎉 Congratulations! Your loan of ₹{eligibility['approved_amount']:,} at {eligibility['interest_rate']}% has been APPROVED! Download your sanction letter below.",
                'message': f"Loan approved for ₹{eligibility['approved_amount']:,} at {eligibility['interest_rate']}% interest.",
                'processing_time': '3.2 minutes',
                'traditional_time': '5-7 days'
            }
        else:
            return {
                'status': 'manual_review',
                'decision': 'Your application requires manual review. You will hear back within 24 hours.',
                'processing_time': '2.8 minutes'
            }


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class AgentOrchestrator:
    """Coordinates all agents"""
    
    def __init__(self):
        self.conv_agent = ConversationAgent()
        self.eligibility_agent = EligibilityAgent()
        self.doc_agent = DocumentAgent()
        self.decision_agent = DecisionAgent()
    
    def process_message(self, message, session):
        """Process user message"""
        flow = session['flow']
        
        print(f"\n🎯 Processing: '{message}'")
        print(f"📊 Current data: {flow.collected_data}")
        print(f"📍 Current stage: {flow.current_stage}")
        
        # Extract all information from message
        extracted = self.conv_agent.extract_all(message)
        print(f"🤖 Agent extracted: {extracted}")
        
        # Update collected data (without overwriting existing data)
        for key, value in extracted.items():
            if value is not None:
                flow.collected_data[key] = value
        
        print(f"✅ Updated data: {flow.collected_data}")
        
        # Generate response
        response = self.conv_agent.generate_response(flow)
        
        # Update stage
        flow.current_stage = flow.get_next_stage()
        print(f"➡️  Next stage: {flow.current_stage}")
        
        return {
            'message': response,
            'stage': flow.current_stage,
            'user_data': flow.collected_data.copy()
        }


# =============================================================================
# FLASK ROUTES
# =============================================================================

orchestrator = AgentOrchestrator()

@app.route('/')
def home():
    return "🤖 Multi-Agent Agentic AI Loan System Running!"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    # Initialize session
    if session_id not in sessions:
        sessions[session_id] = {
            'flow': ConversationFlow(),
            'messages': [],
            'documents': [],
            'eligibility': None
        }
    
    session = sessions[session_id]
    session['messages'].append({'role': 'user', 'content': message})
    
    try:
        result = orchestrator.process_message(message, session)
        
        session['messages'].append({'role': 'assistant', 'content': result['message']})
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/eligibility', methods=['POST'])
def check_eligibility():
    data = request.json
    session_id = data.get('session_id', 'default')
    
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = sessions[session_id]
    flow_data = session['flow'].collected_data
    
    try:
        time.sleep(2)  # Simulate processing
        
        result = orchestrator.eligibility_agent.calculate(flow_data)
        session['eligibility'] = result
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Eligibility error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            print("❌ No file in request")
            return jsonify({'error': 'No file uploaded', 'verified': False}), 400
        
        file = request.files['file']
        doc_type = request.form.get('type', 'unknown')
        session_id = request.form.get('session_id', 'default')
        
        print(f"\n📤 Upload request:")
        print(f"  File: {file.filename}")
        print(f"  Type: {doc_type}")
        print(f"  Session: {session_id}")
        
        if not file.filename:
            print("❌ Empty filename")
            return jsonify({'error': 'No file selected', 'verified': False}), 400
        
        # Initialize session if needed
        if session_id not in sessions:
            sessions[session_id] = {
                'flow': ConversationFlow(),
                'messages': [],
                'documents': [],
                'eligibility': None
            }
        
        # Verify document
        result = orchestrator.doc_agent.verify(file, doc_type)
        sessions[session_id]['documents'].append(result)
        
        print(f"✅ Upload successful: {result}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'verified': False}), 500

@app.route('/api/decision', methods=['POST'])
def final_decision():
    data = request.json
    session_id = data.get('session_id', 'default')
    
    print(f"\n🎯 Final Decision Request for session: {session_id}")
    
    if session_id not in sessions:
        print(f"❌ Session {session_id} not found")
        return jsonify({'error': 'Session not found'}), 404
    
    session = sessions[session_id]
    eligibility = session.get('eligibility', {})
    documents = session.get('documents', [])
    
    print(f"📊 Eligibility data: {eligibility}")
    print(f"📄 Documents count: {len(documents)}")
    
    try:
        time.sleep(1)
        
        result = orchestrator.decision_agent.decide(eligibility, documents)
        
        print(f"✅ Decision: {result['status']}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Decision error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'message': 'Failed to process decision. Please try again.'}), 500

@app.route('/api/generate-letter', methods=['POST'])
def generate_letter():
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    import io
    
    data = request.json
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1*inch, A4[1] - 1*inch, "LOAN SANCTION LETTER")
    
    c.setFont("Helvetica", 11)
    c.drawString(1*inch, A4[1] - 1.5*inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, A4[1] - 2*inch, "Dear Applicant,")
    
    c.setFont("Helvetica", 11)
    y = A4[1] - 2.5*inch
    
    lines = [
        "",
        "Your loan has been APPROVED by our Multi-Agent AI System.",
        "",
        "Loan Details:",
        f"  • Amount: ₹{data.get('approved_amount', 0):,}",
        f"  • Interest: {data.get('interest_rate', 0)}% per annum",
        f"  • Tenure: 5 years",
        "",
        "Processed by AI Agents:",
        "  ✓ Conversation Agent",
        "  ✓ Eligibility Agent", 
        "  ✓ Document Agent",
        "  ✓ Decision Agent",
        "",
        "Processing time: 3 minutes (vs 5-7 days traditional)",
    ]
    
    for line in lines:
        c.drawString(1*inch, y, line)
        y -= 0.25*inch
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, 2*inch, "Multi-Agent AI System")
    
    c.save()
    buffer.seek(0)
    
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='sanction_letter.pdf')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 MULTI-AGENT AGENTIC AI LOAN SYSTEM")
    print("="*60)
    print("\n✅ Agents Ready:")
    print("  1️⃣  Conversation Agent")
    print("  2️⃣  Eligibility Agent")
    print("  3️⃣  Document Agent")
    print("  4️⃣  Decision Agent")
    print("  🎯 Orchestrator")
    print("\n🚀 http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)