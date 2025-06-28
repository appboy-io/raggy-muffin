import streamlit as st
from config import config

def product_page():
    # Hero Section
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">{config.APP_ICON} {config.APP_NAME}</h1>
        <h2 style="color: {config.SECONDARY_COLOR}; font-weight: 300; margin-bottom: 2rem;">
            {config.APP_TAGLINE}
        </h2>
        <p style="font-size: 1.2rem; color: #888; max-width: 600px; margin: 0 auto;">
            {config.APP_DESCRIPTION}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(f"🚀 {config.CTA_PRIMARY_TEXT}", type="primary", use_container_width=True):
            st.session_state.selected_page = "📁 Upload Workflow"
            st.rerun()
        
        st.markdown(f'<p style="text-align: center; color: {config.SECONDARY_COLOR}; margin-top: 0.5rem;">{config.CTA_TRIAL_TEXT}</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Social Proof
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <p style="color: #888; font-size: 0.9rem;">
            {config.SOCIAL_PROOF_TEXT}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Benefits
    st.markdown(f"## Why Choose {config.APP_NAME}?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        ### {config.FEATURE_1_ICON} **{config.FEATURE_1_TITLE}**
        {config.FEATURE_1_DESC}
        
        *"{config.FEATURE_1_QUOTE}"*
        """)
    
    with col2:
        st.markdown(f"""
        ### {config.FEATURE_2_ICON} **{config.FEATURE_2_TITLE}**
        {config.FEATURE_2_DESC}
        
        *"{config.FEATURE_2_QUOTE}"*
        """)
    
    with col3:
        st.markdown(f"""
        ### {config.FEATURE_3_ICON} **{config.FEATURE_3_TITLE}**
        {config.FEATURE_3_DESC}
        
        *"{config.FEATURE_3_QUOTE}"*
        """)
    
    st.markdown("---")
    
    # How It Works
    st.markdown("## How It Works")
    
    col1, col2, col3, col4 = st.columns(4)
    steps = config.get_how_it_works_steps()
    
    for i, (step, col) in enumerate(zip(steps, [col1, col2, col3, col4])):
        with col:
            st.markdown(f"""
            ### {step['number']}. {step['icon']} {step['title']}
            {step['desc']}
            {step['details']}
            """)
    
    st.markdown("---")
    
    # Pricing Preview
    st.markdown("## Simple, Transparent Pricing")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    features_list = '\n'.join([f'<li>{feature}</li>' for feature in config.get_starter_plan_features()])
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; border: 2px solid #e0e0e0; border-radius: 10px; padding: 2rem; background: {config.ACCENT_COLOR};">
            <h3>Starter Plan</h3>
            <h2 style="color: {config.PRIMARY_COLOR};">{config.STARTER_PLAN_PRICE}/{config.STARTER_PLAN_PERIOD}</h2>
            <ul style="text-align: left; list-style: none; padding: 0;">
                {features_list}
            </ul>
            <p style="color: {config.SECONDARY_COLOR}; font-size: 0.9rem; margin-top: 1rem;">
                Perfect for individual researchers and small teams
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<p style="text-align: center; margin-top: 1rem;"><a href="#" style="color: {config.PRIMARY_COLOR};">View all plans →</a></p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Success Stories
    st.markdown("## What Our Users Say")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        > *"{config.TESTIMONIAL_1_TEXT}"*
        
        **{config.TESTIMONIAL_1_AUTHOR}** - {config.TESTIMONIAL_1_TITLE}
        """)
    
    with col2:
        st.markdown(f"""
        > *"{config.TESTIMONIAL_2_TEXT}"*
        
        **{config.TESTIMONIAL_2_AUTHOR}** - {config.TESTIMONIAL_2_TITLE}
        """)
    
    st.markdown("---")
    
    # Final CTA
    st.markdown("## Ready to Transform Your Research?")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    trial_benefits = config.get_trial_benefits()
    benefits_text = '<br>'.join([f"✅ {benefit.replace('✅ ', '')}" for benefit in trial_benefits[:3]])
    
    with col2:
        if st.button(f"🚀 {config.CTA_SECONDARY_TEXT}", type="primary", use_container_width=True):
            st.session_state.selected_page = "📁 Upload Workflow"
            st.rerun()
        
        st.markdown(f"""
        <div style="text-align: center; margin-top: 1rem;">
            <p style="color: {config.SECONDARY_COLOR}; font-size: 0.9rem;">
                {benefits_text}
            </p>
        </div>
        """, unsafe_allow_html=True)