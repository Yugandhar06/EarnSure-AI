MicroShield – AI-Powered Income Protection for Gig Workers

Overview
MicroShield is a real-time, usage-based income protection system designed for gig workers like delivery partners and drivers.

Workers only pay when they are actively working, and receive fair compensation when external disruptions (weather, pollution, traffic, app outages) impact their earnings.

The system combines risk-based pricing (SafarScore), AI-driven income prediction (PEB), and advanced fraud prevention mechanisms to ensure fairness, transparency, and scalability.

Persona-Based Scenarios & Workflow

Persona 1: Ravi (Delivery Partner)
- Works on platforms like Swiggy/Zomato
- Income varies due to weather, demand, and app issues
- Needs protection against unpredictable earnings

How Ravi uses MicroShield:**
1. Opens app and clicks **"Start Shift"**
2. MicroShield activates coverage
3. Pays small hourly premium based on risk
4. If disruption occurs → gets compensated automatically

Persona 2: Platform/Insurer
- Wants scalable, fraud-resistant micro-insurance model
- Needs accurate risk and payout calculation

Benefits:
- Reduced fraud via multi-signal validation
- Dynamic pricing based on real-world conditions
- AI-driven fair payouts



Workflow

1. SafarScore Engine (Live Risk Score)
   - Updates every 15 minutes (0–100 scale)
   - Based on:
     - Weather 🌧
     - AQI 🌫
     - Traffic 🚦
     - App outages 📱

2. Start Shift (MicroShield)**
   - User activates coverage
   - Premium charged per hour

3. Dynamic Pricing
   | Score | Risk Level | Price/hour    |
   |-------|-------------|--------------|
   | 0–30  | Low         | ₹3/hr        |
   | 31–60 | Medium      | ₹5/hr        |
   | 61–80 | High        | ₹7/hr        |
   | 81–100| Extreme     | ₹9/hr        |

4. AI-Based Personal Earning Baseline (PEB)
   - Learns user’s past earnings
   - Considers:
     - Time of day
     - Location
     - Work patterns
   - Example:
     - Morning → ₹300
     - Night → ₹900

Weekly Premium Model

- Users pay **only during active shifts**
- Weekly cost depends on:
  - Hours worked
  - Risk level (SafarScore)

Parametric Triggers
- SafarScore > 60 activates payout eligibility
- External disruptions must be detected

Why Web Platform?
- Faster deployment for hackathon
- Easy dashboard for real-time monitoring
- Scalable to mobile in future phases

AI/ML Integration

1. Premium & Income Prediction
- AI calculates **Personal Earning Baseline (PEB)**
- Uses historical earnings + behavioral patterns

2. Fraud Detection (Core Innovation)
3-Signal Validation System:
At least 2 of the following must match:
- External signal (weather, AQI, outage)
- GPS activity drop
- Demand/order drop

3.Dynamic Effort Rule
| Severity | Required Effort |
|---------|----------------|
| Low     | 3 orders       |
| Medium  | 2 orders       |
| High    | 1 order        |
| Extreme | 0 orders       |

Ensures fairness and prevents misuse

4. Future AI Scope
- Advanced anomaly detection
- Behavioral fraud patterns
- Predictive risk alerts

 Payout Formula

Coverage Plans:
- Basic → 50%
- Standard → 60%
- Premium → 70%
- Max → 80%

Example Scenarios

Heavy Rain
- PEB = ₹800, Actual = ₹300
- Loss = ₹500  
- Payout = ₹300

Heat Wave
- Loss = ₹700  
- Payout = ₹420  

Pollution
- No work possible  
- Payout = ₹420  

App Crash
- Partial income loss  
- Payout = ₹180  

No Disruption
- No payout → Fraud prevented

Fraud Prevention System (Strongest Feature)

- Shift must start before disruption
- Tier locked before event
- 3-signal validation
- Dynamic effort rule
- GPS tracking
- Platform demand verification
- Aadhaar linking
- AI-based anomaly detection


Tech Stack
Frontend: React.js, HTML, CSS  
Backend: Node.js / Spring Boot  
Database: MySQL / MongoDB  
Cloud & Deployment: AWS, Docker  
AI/ML: Python, TensorFlow  

Development Plan

Phase 1 (Hackathon MVP)
- Basic SafarScore engine
- Shift activation system
- Simple payout logic

Phase 2
- Real-time data integration (weather, traffic APIs)
- Dashboard for users

Phase 3
- Full AI/ML models (PEB + fraud detection)
- Mobile app deployment
- Scaling infrastructure

Key Innovation

- Pay-per-use insurance model
- Real-time risk scoring (SafarScore)
- AI-driven personalized payouts
- Multi-layer fraud prevention system

Future Scope
- Integration with gig platforms (Swiggy, Zomato, Uber)
- Government partnerships
- Expansion to global gig economy
