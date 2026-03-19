ShiftSafe — AI-Powered Parametric Income Protection for India's Gig Delivery Workers

"We don't wait for riders to file claims. We watch the city, verify genuine effort, and send money to their phone before they even ask."

The Problem :

India has 15 million+ gig delivery workers on Zomato, Swiggy, Zepto, Amazon, and Blinkit.
On a heavy rain day, a flooded road day, or a platform outage day — they earn zero.
No safety net. No claim process. No protection.

They borrow from moneylenders at 3% per week to survive the gap.
ShiftSafe fixes this.

What We Built

A fully automated parametric income protection platform for food delivery riders (Zomato/Swiggy), built specifically for Indian gig work conditions.
->Not traditional insurance. A guaranteed income floor backed by AI.
->When the world disrupts a rider's ability to earn — rain, extreme heat, bad air, platform crash — ShiftSafe detects it automatically, verifies the rider genuinely tried to work, and tops up their income to their personal earning baseline.
->Zero claim forms. Zero waiting. Money arrives in under 90 seconds.

Field	                    Detail
Worker type	       :  Food delivery riders — Zomato & Swiggy
Cities	           :  Bengaluru, Delhi, Mumbai (metro-first MVP)
Vehicle	           :  2-wheeler (bike/scooter)
Daily earnings	   :  ₹600 – ₹1,500 depending on hours and zone
Monthly earnings   :  ₹18,000 – ₹45,000
Key vulnerability  :  Weather, AQI, app outages wipe out 20–30% of monthly income

Subscription Plans
ShiftSafe offers four weekly subscription tiers — one fixed plan for brand-new riders and three earnings-linked plans for active riders. Every plan is auto-debited every Monday via UPI AutoPay. No lock-in. Pause or cancel any week. Upgrade or downgrade takes effect the following Monday.

New rider (0–2 weeks active)        	(fixed ₹29/week)
Weekly earnings ₹1,500 – ₹3,000	         BASIC plan   (₹49/week)
Weekly earnings  ₹3,001 – ₹5,000	 PLUS plan    (₹89/week)   ← most riders
Weekly earnings ₹5,001 –₹8,400	         PRO plan     (₹149/week)

Tier is auto-calculated every Monday based on prior 4-week average earnings.
Rider is notified of tier change 3 days before it applies.
Riders can manually lock to a lower tier if they prefer lower premium.

STARTER — ₹29/week
Who gets this: Any rider in their first 14 days on ShiftSafe.
Duration: Weeks 1–2 only. Auto-upgrades to earnings-linked tier from Week 3.
Weekly premium        : ₹29
Coverage ratio        : 40%
Max daily top-up      : ₹250
Max weekly top-up     : ₹1,000
Disruption triggers   : 2
PEB model             : Zone average only
Payout speed          : < 6 hours
Multi-app tracking    : Single platform
WhatsApp alerts       : Post-event
Dispute window        : 12 hours

BASIC — ₹49/week
Who gets this         : Riders earning ₹1,500 – ₹3,000/week.
Weekly premium        : ₹49 base
Coverage ratio        : 50%
Max daily top-up      : ₹400
Max weekly top-up     : ₹1,600
Disruption triggers   : 2
PEB model             : Cluster → Personal
Payout speed          : < 4 hours
Multi-app tracking    : Single platform
WhatsApp alerts       : Post-event
Dispute window        : 12 hours

PLUS — ₹89/week
Who gets this         : Riders earning ₹3,001 – ₹5,000/week.
Weekly premium        : ₹89 base
Coverage ratio        : 60%
Max daily top-up      : ₹700
Max weekly top-up     : ₹2,800
Disruption triggers   : 4
PEB model             : Personal 90-day model
Payout speed          : < 90 seconds
Multi-app tracking    : 2 platforms
WhatsApp alerts       : Pre + Post
Dispute window        : 24 hours


PRO — ₹149/week
Who gets this         : Riders earning ₹5,001 – ₹8,400/week.
Weekly premium        : ₹149 base
Coverage ratio        : 75%
Max daily top-up      : ₹1,100
Max weekly top-up     : ₹4,400
Disruption triggers   : 4 + v2
PEB model             : Personal + predictive model
Payout speed          : < 60 seconds
Multi-app tracking    : All platforms
WhatsApp alerts       : Real-time
Dispute window        : 48 hours

Full Tier Comparison :

	           STARTER ₹29/wk | BASIC₹49/wk	| PLUS ₹89/wk | PRO ₹149/wk
Coverage ratio	  :      40%  |    50%	    |   60%	      |    75%
Max daily top-up  :	    ₹250  |   ₹250	    |  ₹250	      |    ₹250
Max weekly top-up :    	₹250  |   ₹250	    |  ₹250	      |    ₹250
Payout speed	  :    < 6 hrs|  < 6 hrs	| < 6 hrs     |   < 6 hrs

Premium as % of Weekly Income
STARTER  : ₹29 / ₹0 (new, no earnings yet)    → Fixed flat entry price
BASIC    : ₹49 / ₹2,250 avg                   → 2.2% of weekly income
PLUS     : ₹89 / ₹4,200 avg                   → 2.1% of weekly income
PRO      : ₹149 / ₹7,000 avg                  → 2.1% of weekly income


Core Innovation
Auto-Detect Mode
IF rider.goes_online():
session = auto_detect_from_gps()
coverage = ACTIVE

Personal Earning Baseline (PEB)
IF rider.days_active < 7:
PEB = zone_cluster_average
ELIF rider.days_active < 15:
PEB = peer_cluster_model
ELSE:
PEB = personal_model

Top-up = PEB − actual_earnings

Dynamic MPE :
Severity	    Orders Required
Low	                  3
Medium	              2
High	              1
Extreme	              0

3-Signal Validation :

IF NOT external_signal:
    payout = BLOCKED

IF external + gps + demand:
payout = FULL

Fraud Prevention :

Layer	Mechanism
L1	    Dynamic MPE
L2   	3-Signal Validation
L3  	GPS Analysis
L4	    Device Fingerprint
L5	    Anomaly Detection

Payout Flow :

Step 1   Disruption detected
Step 2   External validation
Step 3   3-signal check
Step 4   MPE check
Step 5   Earnings calculated
Step 6   PEB fetched
Step 7   Top-up calculated
Step 8   Fraud check
Step 9   UPI transfer

Time: < 90 seconds

Layer	        Technology
Frontend	React Native
Backend	    NestJS
ML	        Python, XGBoost
Database	PostgreSQL, Redis
Payments	Razorpay
Infra	    AWS, Docker



