from langchain_core.prompts import ChatPromptTemplate

adaptive_product_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an AI personalization engine. 
You generate adaptive product descriptions with:

- Header
- Subheader
- Tagline
- Summary
- Visual cues
- CTA
- Metatags
- Social proof
- Hyperlink label

Output valid JSON.

"""
    ),
    ("human", "User attributes: {user_profile}\nProduct: {product}")
])