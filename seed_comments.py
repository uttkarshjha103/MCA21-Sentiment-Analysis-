"""Seed 100 comments directly into MongoDB."""
import asyncio
from datetime import datetime, timedelta
import random
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "mca21_sentiment_analysis"

positive = [
    "This policy is a landmark achievement for corporate governance in India. I fully support it.",
    "The digital transformation of MCA21 is excellent. Filing is now fast and transparent.",
    "Outstanding work by the ministry. These reforms will attract foreign investment.",
    "I am very happy with the new shareholder protection clauses. Long overdue.",
    "The simplified compliance process is a relief for honest businesses. Thank you.",
    "This is exactly what India needed. Corporate accountability will improve greatly.",
    "The new audit framework is robust and well thought out. Highly commendable.",
    "Excellent initiative. The online portal is user-friendly and efficient.",
    "I strongly support these amendments. They protect minority shareholders effectively.",
    "The transparency measures are world-class. India is moving in the right direction.",
    "Brilliant policy! ESG reporting requirements will make companies more responsible.",
    "The ministry has done a fantastic job. These regulations are fair and balanced.",
    "I love the new whistleblower protection provisions. Very progressive.",
    "The board composition requirements will bring diversity and better governance.",
    "This is a great step forward. The penalties are proportionate and just.",
    "The consultation process was inclusive and the final policy reflects our feedback.",
    "Wonderful reforms! The digital filing system saves time and reduces corruption.",
    "I am impressed by the thoroughness of these regulations. Well done.",
    "The new related party transaction rules are clear and will prevent abuse.",
    "These amendments will make India a top destination for global investors.",
    "The ministry has listened to stakeholders. This is a balanced and fair policy.",
    "Excellent work. The corporate governance standards are now world-class.",
    "I fully endorse these reforms. They will strengthen the Indian economy.",
    "The new disclosure requirements are comprehensive and necessary.",
    "This policy will reduce corporate fraud significantly. Very welcome.",
    "The streamlined processes will help businesses focus on growth, not paperwork.",
    "I appreciate the ministry for considering MSME concerns in the final draft.",
    "The new framework is progressive and forward-thinking. Highly supportive.",
    "These regulations strike the right balance between compliance and ease of business.",
    "The digital infrastructure improvements are impressive. Great initiative.",
    "I support this policy wholeheartedly. It will benefit all stakeholders.",
    "The new investor protection measures are strong and effective.",
    "Excellent policy design. The implementation guidelines are clear and practical.",
    "This is a positive development for Indian corporate sector. Well done ministry.",
    "The reforms are timely and necessary. I am optimistic about their impact.",
]

negative = [
    "This policy is a disaster for small businesses. The compliance costs are unbearable.",
    "The ministry has completely ignored industry feedback. Very disappointing.",
    "These regulations are poorly drafted and full of contradictions.",
    "The implementation timeline is impossible. No company can comply in 3 months.",
    "The penalties are draconian and disproportionate. This will harm businesses.",
    "I strongly oppose these amendments. They will drive companies out of India.",
    "The compliance burden is astronomical. MSMEs will be forced to shut down.",
    "This is the worst corporate policy in years. Completely impractical.",
    "The ministry has failed to understand ground realities. Very frustrating.",
    "These rules will create massive legal uncertainty and endless litigation.",
    "The quarterly audit requirements are excessive and unnecessary.",
    "I am deeply concerned about the impact on startup ecosystem. Very harmful.",
    "The new regulations are bureaucratic nightmares. Please reconsider.",
    "The ministry has not consulted industry adequately. Top-down approach.",
    "These amendments will increase corruption, not reduce it. Poorly designed.",
    "The documentation requirements are absurd. No business can manage this.",
    "I oppose this policy strongly. It punishes honest businesses unfairly.",
    "The related party transaction rules are confusing and unworkable.",
    "This will destroy the ease of doing business in India. Very bad policy.",
    "The penalties for minor violations are completely out of proportion.",
    "The ministry has created a compliance monster. Businesses will suffer.",
    "These regulations show no understanding of how businesses actually work.",
    "I am appalled by the lack of consultation with affected industries.",
    "The new audit framework is burdensome and adds no real value.",
    "This policy will push companies to register in other countries. Terrible.",
    "The implementation costs are prohibitive for medium-sized enterprises.",
    "These rules are designed by bureaucrats who have never run a business.",
    "The new disclosure requirements are invasive and unnecessary.",
    "I strongly disagree with these amendments. They will harm economic growth.",
    "The ministry has made a serious mistake with this policy. Please withdraw it.",
    "These regulations are anti-business and anti-growth. Very disappointing.",
    "The compliance timeline shows complete disregard for business realities.",
    "I am very unhappy with this policy. It will increase costs for everyone.",
    "The new framework is overly complex and will confuse even experts.",
    "This is a step backward for Indian business environment. Very concerning.",
]

neutral = [
    "The Ministry of Corporate Affairs has released the draft amendments for public review.",
    "The consultation period for the new regulations runs from January to March 2024.",
    "The proposed changes cover board composition, audit requirements, and disclosures.",
    "Stakeholders may submit feedback through the official MCA21 portal.",
    "The amendments affect companies registered under the Companies Act 2013.",
    "Regional workshops are scheduled in Mumbai, Delhi, Chennai, and Kolkata.",
    "The new regulations will come into effect six months after final notification.",
    "The ministry has received over 5000 comments during the consultation period.",
    "The draft covers 47 sections including governance, reporting, and audit procedures.",
    "Companies with turnover above 500 crore will face additional requirements.",
    "The amendments include provisions for digital filing and electronic signatures.",
    "The ministry will review all feedback before finalizing the regulations.",
    "The new framework aligns with international corporate governance standards.",
    "Implementation guidelines will be issued separately after the final notification.",
    "The regulations apply to both listed and unlisted public companies.",
    "Small companies with paid-up capital below 2 crore are partially exempt.",
    "The ministry has formed a committee to oversee the implementation process.",
    "Training programs for compliance officers will be organized by ICAI.",
    "The new portal will be launched simultaneously with the regulation notification.",
    "Companies have the option to seek clarification from the ministry directly.",
    "The amendments were drafted after reviewing corporate governance frameworks globally.",
    "A phased implementation approach has been proposed for complex requirements.",
    "The ministry will publish FAQs to help companies understand the new rules.",
    "Industry associations have been invited to participate in the review process.",
    "The regulations include provisions for annual compliance certification.",
    "The ministry has set up a dedicated helpline for compliance queries.",
    "Companies must update their articles of association within 12 months.",
    "The new framework includes provisions for cross-border transactions.",
    "The ministry will conduct quarterly reviews of the implementation progress.",
    "All listed companies must comply with the new board diversity requirements.",
]

sources = ['public_consultation', 'industry_feedback', 'legal_association',
           'ngo_feedback', 'msme_association', 'investor_forum', 'startup_community',
           'business_council', 'chamber_of_commerce', 'official_portal']

async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    docs = []
    base_date = datetime(2024, 1, 1)

    for i, text in enumerate(positive):
        docs.append({
            'comment_text': text,
            'source': random.choice(sources),
            'date_submitted': base_date + timedelta(days=i),
            'original_language': 'en',
            'metadata': {},
        })

    for i, text in enumerate(negative):
        docs.append({
            'comment_text': text,
            'source': random.choice(sources),
            'date_submitted': base_date + timedelta(days=i + 35),
            'original_language': 'en',
            'metadata': {},
        })

    for i, text in enumerate(neutral):
        docs.append({
            'comment_text': text,
            'source': random.choice(sources),
            'date_submitted': base_date + timedelta(days=i + 70),
            'original_language': 'en',
            'metadata': {},
        })

    result = await db.comments.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} comments")
    client.close()

asyncio.run(seed())
