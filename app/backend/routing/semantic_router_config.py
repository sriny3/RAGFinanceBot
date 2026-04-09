from semantic_router import Route


# Finance Route
finance_route = Route(
    name="finance_route",
    utterances=[
        "What is our Q3 revenue?",
        "How much did we budget for marketing this year?",
        "Show me financial metrics for 2024.",
        "What are our investor relations like?",
        "Can you provide details on ROI?",
        "What's our profit margin?",
        "Tell me about quarterly earnings.",
        "What are our expense allocations?",
        "Show me the annual financial report.",
        "What are vendor payments?",
        "Can you help with budget planning?",
        "What's the cost of goods sold?",
        "Show me our financial projections.",
        "What are our revenue streams?",
        "Tell me about dividend policies.",
    ],
)

# Engineering Route
engineering_route = Route(
    name="engineering_route",
    utterances=[
        "How do I onboard to the platform?",
        "Tell me about our system architecture.",
        "What are our API endpoints?",
        "How do we handle incidents?",
        "Show me the technical specifications.",
        "What's our deployment process?",
        "How do we manage SLAs?",
        "Tell me about our sprint metrics.",
        "What are the incident response procedures?",
        "Can you explain our system design?",
        "Show me the API reference documentation.",
        "How do we do code reviews?",
        "What's our tech stack?",
        "Tell me about infrastructure.",
        "How do we handle system failures?",
    ],
)

# Marketing Route
marketing_route = Route(
    name="marketing_route",
    utterances=[
        "What's our campaign performance?",
        "Tell me about our brand guidelines.",
        "What's our market share?",
        "Who are our competitors?",
        "Show me customer acquisition data.",
        "What are our marketing metrics?",
        "Tell me about our brand positioning.",
        "How are our campaigns performing?",
        "What's our customer acquisition strategy?",
        "Show me competitive analysis.",
        "What are current marketing initiatives?",
        "Tell me about promotional campaigns.",
        "What's our marketing budget?",
        "Show me customer demographics.",
        "What are campaign ROI metrics?",
    ],
)

# HR / General Route
hr_general_route = Route(
    name="hr_general_route",
    utterances=[
        "What are our HR policies?",
        "How much leave am I entitled to?",
        "Tell me about company benefits.",
        "What's the company culture like?",
        "How do I request time off?",
        "What are the company policies?",
        "Tell me about employee handbook.",
        "What benefits do employees get?",
        "How do we handle remote work?",
        "What's the dress code policy?",
        "Tell me about professional development.",
        "What are the vacation policies?",
        "How does health insurance work?",
        "What are parental leave policies?",
        "Tell me about retirement plans.",
    ],
)

# Cross-Department Route (catch-all)
cross_department_route = Route(
    name="cross_department_route",
    utterances=[
        "Tell me about FinSolve Technologies.",
        "What does the company do?",
        "Give me an overview of FinSolve.",
        "What are our company values?",
        "Tell me about our organization.",
        "What's the company mission?",
        "Can you provide general company information?",
        "What is FinSolve?",
        "Tell me about company history.",
        "What sectors do we serve?",
        "What is the purpose of this company?",
        "Tell me about company structure.",
        "What are our core services?",
        "Who are our clients?",
        "What's our competitive advantage?",
    ],
)

# List of all routes for the router
ALL_ROUTES = [
    finance_route,
    engineering_route,
    marketing_route,
    hr_general_route,
    cross_department_route,
]

# Mapping of route names to their priority collections
ROUTE_COLLECTION_MAPPING = {
    "finance_route": ["general", "finance"],
    "engineering_route": ["general", "engineering"],
    "marketing_route": ["general", "marketing"],
    "hr_general_route": ["general", "hr"],
    "cross_department_route": ["general", "finance", "engineering", "marketing", "hr"],
}
