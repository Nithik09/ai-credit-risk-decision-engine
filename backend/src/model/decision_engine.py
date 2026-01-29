"""
Decision Engine for Credit Risk Scoring
Implements approval/rejection logic and risk tier assignment
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import yaml
from loguru import logger
from enum import Enum


class Decision(Enum):
    """Credit decision outcomes."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class RiskTier(Enum):
    """Credit risk tiers for approved applications."""
    A = "A"  # Prime (lowest risk)
    B = "B"  # Near-prime
    C = "C"  # Subprime
    D = "D"  # High risk (typically rejected)


class DecisionEngine:
    """
    Production credit decision engine.
    
    Implements:
    - Approval/rejection logic based on PD thresholds
    - Risk tier assignment (A, B, C, D)
    - Credit limit recommendations
    - Pricing suggestions based on risk
    - Manual review flagging
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize decision engine with configuration."""
        # Handle relative path from different execution contexts
        if not Path(config_path).exists():
            # Try project root
            root_config = Path(__file__).parent.parent.parent / config_path
            if root_config.exists():
                config_path = str(root_config)
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.risk_thresholds = self.config['risk_scoring']
        self.rejection_threshold = self.risk_thresholds['rejection_threshold']
        
        logger.info("DecisionEngine initialized")
        logger.info(f"Rejection threshold: {self.rejection_threshold}")
    
    def _check_excellent_applicant(self, application_data: Optional[Dict]) -> bool:
        """Check if applicant qualifies for excellent applicant override."""
        if not application_data:
            logger.debug("No application_data provided")
            return False
        
        # Check explicit flag
        flag_value = application_data.get('IS_EXCELLENT_APPLICANT')
        logger.info(f"Excellent flag check: IS_EXCELLENT_APPLICANT={flag_value}")
        if flag_value == 1:
            logger.info("✓ Excellent applicant flag detected!")
            return True
        
        # Check criteria
        def _safe_float(value, default: float) -> float:
            try:
                if value is None:
                    return default
                value = float(value)
                if np.isnan(value):
                    return default
                return value
            except Exception:
                return default

        income = _safe_float(application_data.get('income_total'), 0.0)
        loan = _safe_float(application_data.get('credit_amount'), 0.0)
        ext_source_avg = np.mean([
            _safe_float(application_data.get('ext_source_1'), 0.5),
            _safe_float(application_data.get('ext_source_2'), 0.5),
            _safe_float(application_data.get('ext_source_3'), 0.5)
        ])
        
        good_credit = ext_source_avg <= 0.30
        good_income = income > 0 and (income / loan) >= 1.5
        
        logger.info(f"Criteria check: credit={ext_source_avg:.3f}<=0.30={good_credit}, income_ratio={income/loan if loan>0 else 0:.2f}>=1.5={good_income}")
        
        return good_credit and good_income

    
    def make_decision(self, pd_score: float, application_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make credit decision for a single application.
        
        Args:
            pd_score: Probability of default (0-1)
            application_data: Optional application details for additional rules
            
        Returns:
            Dictionary with decision details
        """
        # Check for excellent applicant override
        is_excellent = self._check_excellent_applicant(application_data)
        if is_excellent:
            logger.info(f"Excellent applicant detected - capping risk at 15%")
            pd_score = min(pd_score, 0.15)
        
        # Determine risk tier
        risk_tier = self._assign_risk_tier(pd_score)
        
        # Make approval decision
        if pd_score > self.rejection_threshold:
            decision = Decision.REJECTED
            credit_limit = 0
            interest_rate = None
            reason = f"PD score {pd_score:.2%} exceeds rejection threshold {self.rejection_threshold:.2%}"
        else:
            decision = Decision.APPROVED
            
            # Calculate credit limit based on risk tier
            credit_limit = self._calculate_credit_limit(risk_tier, application_data)
            
            # Calculate interest rate based on risk
            interest_rate = self._calculate_interest_rate(pd_score, risk_tier)
            
            reason = f"PD score {pd_score:.2%} is acceptable for {risk_tier.value} tier"
        
        # Check for manual review conditions
        manual_review_required, review_reasons = self._check_manual_review(
            pd_score, application_data
        )
        
        # Override manual review for excellent applicants
        if manual_review_required and is_excellent:
            logger.info(f"Skipping manual review for excellent applicant")
            manual_review_required = False
            review_reasons = []
        
        if manual_review_required:
            decision = Decision.MANUAL_REVIEW
        
        result = {
            'decision': decision.value,
            'pd_score': pd_score,
            'risk_tier': risk_tier.value,
            'credit_limit': credit_limit,
            'interest_rate': interest_rate,
            'decision_reason': reason,
            'manual_review_required': manual_review_required,
            'manual_review_reasons': review_reasons
        }
        
        return result
    
    def _assign_risk_tier(self, pd_score: float) -> RiskTier:
        """
        Assign risk tier based on PD score.
        
        Args:
            pd_score: Probability of default
            
        Returns:
            RiskTier enum
        """
        tier_ranges = self.risk_thresholds['tiers']
        
        for tier_name, (min_pd, max_pd) in tier_ranges.items():
            if min_pd <= pd_score < max_pd:
                return RiskTier[tier_name]
        
        return RiskTier.D  # Default to highest risk
    
    def _calculate_credit_limit(self, risk_tier: RiskTier, 
                               application_data: Optional[Dict] = None) -> float:
        """
        Calculate recommended credit limit based on risk tier and application data.
        
        Args:
            risk_tier: Assigned risk tier
            application_data: Application details (income, etc.)
            
        Returns:
            Recommended credit limit
        """
        # Base limits by tier
        base_limits = {
            RiskTier.A: 50000,
            RiskTier.B: 25000,
            RiskTier.C: 10000,
            RiskTier.D: 0
        }
        
        base_limit = base_limits.get(risk_tier, 0)
        
        # Adjust based on income if available
        if application_data and 'income' in application_data:
            income = application_data['income']
            # Credit limit should not exceed 3x annual income
            max_limit_by_income = income * 3
            base_limit = min(base_limit, max_limit_by_income)
        
        return base_limit
    
    def _calculate_interest_rate(self, pd_score: float, risk_tier: RiskTier) -> float:
        """
        Calculate risk-based interest rate (APR).
        
        Uses risk-based pricing: higher PD → higher interest rate
        
        Args:
            pd_score: Probability of default
            risk_tier: Risk tier
            
        Returns:
            Annual percentage rate (APR)
        """
        # Base rates by tier (APR %)
        base_rates = {
            RiskTier.A: 8.0,   # Prime rate
            RiskTier.B: 15.0,  # Near-prime
            RiskTier.C: 22.0,  # Subprime
            RiskTier.D: 30.0   # High risk
        }
        
        base_rate = base_rates.get(risk_tier, 30.0)
        
        # Add risk premium based on PD within tier
        # Higher PD within tier → higher rate
        risk_premium = pd_score * 20  # Up to 20% premium for very high PD
        
        apr = base_rate + risk_premium
        
        # Cap at maximum legal rate (e.g., 36% in many states)
        apr = min(apr, 36.0)
        
        return round(apr, 2)
    
    def _check_manual_review(self, pd_score: float,
                            application_data: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        """
        Check if application requires manual review.
        
        Args:
            pd_score: Probability of default
            application_data: Application details
            
        Returns:
            Tuple of (requires_review, reasons)
        """
        reasons = []
        
        # 1. PD near boundary (within 2% of rejection threshold)
        if abs(pd_score - self.rejection_threshold) < 0.02:
            reasons.append("PD score near rejection boundary")
        
        # 2. Very high credit amount requested
        if application_data and 'credit_amount' in application_data:
            if application_data['credit_amount'] > 100000:
                reasons.append("Unusually high credit amount requested")
        
        # 3. Inconsistent data
        if application_data:
            # Example: Credit amount much larger than income
            if 'credit_amount' in application_data and 'income' in application_data:
                if application_data['credit_amount'] > application_data['income'] * 5:
                    reasons.append("Credit amount significantly exceeds income")
        
        # 4. Missing critical external scores
        if application_data and 'external_score' in application_data:
            if application_data['external_score'] is None or pd.isna(application_data['external_score']):
                reasons.append("Missing critical external credit score")
        
        requires_review = len(reasons) > 0
        
        return requires_review, reasons
    
    def batch_decisions(self, df: pd.DataFrame, pd_col: str = 'pd_score',
                       include_application_data: bool = False) -> pd.DataFrame:
        """
        Make decisions for batch of applications.
        
        Args:
            df: DataFrame with PD scores and application data
            pd_col: Column name for PD scores
            include_application_data: Whether to use application data for decisions
            
        Returns:
            DataFrame with decision details
        """
        logger.info(f"Processing {len(df)} applications...")
        
        decisions = []
        
        for idx, row in df.iterrows():
            pd_score = row[pd_col]
            
            # Get application data if requested
            app_data = None
            if include_application_data:
                app_data = {
                    'income': row.get('AMT_INCOME_TOTAL', None),
                    'credit_amount': row.get('AMT_CREDIT', None),
                    'external_score': row.get('EXT_SOURCE_2', None)
                }
            
            # Make decision
            decision = self.make_decision(pd_score, app_data)
            decisions.append(decision)
        
        # Convert to DataFrame
        decisions_df = pd.DataFrame(decisions)
        
        # Combine with original data
        result_df = pd.concat([df.reset_index(drop=True), decisions_df], axis=1)
        
        # Log summary
        self._log_batch_summary(decisions_df)
        
        return result_df
    
    def _log_batch_summary(self, decisions_df: pd.DataFrame) -> None:
        """Log summary statistics for batch decisions."""
        total = len(decisions_df)
        
        approved = (decisions_df['decision'] == Decision.APPROVED.value).sum()
        rejected = (decisions_df['decision'] == Decision.REJECTED.value).sum()
        manual_review = (decisions_df['decision'] == Decision.MANUAL_REVIEW.value).sum()
        
        logger.info("\n" + "="*60)
        logger.info("BATCH DECISION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Applications: {total}")
        logger.info(f"Approved: {approved} ({approved/total*100:.1f}%)")
        logger.info(f"Rejected: {rejected} ({rejected/total*100:.1f}%)")
        logger.info(f"Manual Review: {manual_review} ({manual_review/total*100:.1f}%)")
        
        # Risk tier distribution (for approved)
        if 'risk_tier' in decisions_df.columns:
            logger.info("\nRisk Tier Distribution (Approved):")
            tier_dist = decisions_df[decisions_df['decision'] == Decision.APPROVED.value]['risk_tier'].value_counts()
            for tier, count in tier_dist.items():
                logger.info(f"  Tier {tier}: {count} ({count/approved*100:.1f}%)")
        
        # Average credit limits and rates
        if 'credit_limit' in decisions_df.columns:
            approved_df = decisions_df[decisions_df['decision'] == Decision.APPROVED.value]
            if len(approved_df) > 0:
                avg_limit = approved_df['credit_limit'].mean()
                avg_rate = approved_df['interest_rate'].mean()
                logger.info(f"\nAverage Credit Limit (Approved): ${avg_limit:,.0f}")
                logger.info(f"Average Interest Rate (Approved): {avg_rate:.2f}%")
    
    def get_decision_distribution(self, decisions_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get detailed distribution statistics for decisions.
        
        Args:
            decisions_df: DataFrame with decision results
            
        Returns:
            Dictionary with distribution statistics
        """
        stats = {
            'total_applications': len(decisions_df),
            'decisions': decisions_df['decision'].value_counts().to_dict(),
            'risk_tiers': decisions_df['risk_tier'].value_counts().to_dict(),
            'approval_rate': (decisions_df['decision'] == Decision.APPROVED.value).mean(),
            'rejection_rate': (decisions_df['decision'] == Decision.REJECTED.value).mean(),
        }
        
        # Statistics for approved applications
        approved_df = decisions_df[decisions_df['decision'] == Decision.APPROVED.value]
        if len(approved_df) > 0:
            stats['approved_stats'] = {
                'count': len(approved_df),
                'avg_credit_limit': approved_df['credit_limit'].mean(),
                'median_credit_limit': approved_df['credit_limit'].median(),
                'avg_interest_rate': approved_df['interest_rate'].mean(),
                'median_interest_rate': approved_df['interest_rate'].median(),
                'avg_pd_score': approved_df['pd_score'].mean()
            }
        
        # Statistics for rejected applications
        rejected_df = decisions_df[decisions_df['decision'] == Decision.REJECTED.value]
        if len(rejected_df) > 0:
            stats['rejected_stats'] = {
                'count': len(rejected_df),
                'avg_pd_score': rejected_df['pd_score'].mean(),
                'median_pd_score': rejected_df['pd_score'].median()
            }
        
        return stats
    
    def export_decisions(self, decisions_df: pd.DataFrame, 
                        output_path: str, format: str = 'csv') -> None:
        """
        Export decisions to file.
        
        Args:
            decisions_df: DataFrame with decisions
            output_path: Output file path
            format: Output format ('csv', 'json', 'excel')
        """
        if format == 'csv':
            decisions_df.to_csv(output_path, index=False)
        elif format == 'json':
            decisions_df.to_json(output_path, orient='records', indent=2)
        elif format == 'excel':
            decisions_df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Decisions exported to {output_path}")


if __name__ == "__main__":
    logger.info("Decision Engine module loaded successfully")
