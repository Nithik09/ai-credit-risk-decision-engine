"""
API Testing Script
Tests the deployed Credit Risk API
"""

import requests
import json
from typing import Dict, Any
import pandas as pd


API_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("\n" + "="*60)
    print("Testing Health Check...")
    print("="*60)
    
    response = requests.get(f"{API_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"✅ Model Loaded: {data['model_loaded']}")
        print(f"✅ Model Version: {data['model_version']}")
        print(f"✅ Uptime: {data['uptime_seconds']:.2f} seconds")
    else:
        print(f"❌ Health check failed: {response.status_code}")
    
    return response.status_code == 200


def test_model_info():
    """Test model info endpoint."""
    print("\n" + "="*60)
    print("Testing Model Info...")
    print("="*60)
    
    response = requests.get(f"{API_URL}/model/info")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Model Version: {data['version']}")
        print(f"✅ Features: {data['features']}")
        print(f"✅ Algorithm: {data['algorithm']}")
        
        if 'validation_metrics' in data and data['validation_metrics']:
            metrics = data['validation_metrics']
            print(f"\nValidation Metrics:")
            print(f"  • AUC: {metrics.get('auc', 'N/A'):.4f}" if metrics.get('auc') else "  • AUC: N/A")
            print(f"  • Gini: {metrics.get('gini', 'N/A'):.4f}" if metrics.get('gini') else "  • Gini: N/A")
    else:
        print(f"❌ Model info failed: {response.status_code}")
    
    return response.status_code == 200


def test_single_scoring():
    """Test single application scoring."""
    print("\n" + "="*60)
    print("Testing Single Application Scoring...")
    print("="*60)
    
    # Example application (prime candidate)
    application = {
        "application_id": "TEST_001",
        "age": 35,
        "gender": "M",
        "income_total": 180000,
        "credit_amount": 50000,
        "annuity_amount": 2500,
        "days_employed": -1825,  # 5 years
        "ext_source_1": 0.75,
        "ext_source_2": 0.80,
        "ext_source_3": 0.70
    }
    
    print("\nApplication Details:")
    print(f"  • Income: ${application['income_total']:,}")
    print(f"  • Credit Amount: ${application['credit_amount']:,}")
    print(f"  • Age: {application['age']}")
    print(f"  • External Score 2: {application['ext_source_2']}")
    
    response = requests.post(f"{API_URL}/score", json=application)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ Scoring Successful!")
        print(f"\nResults:")
        print(f"  • PD Score: {result['pd_score']:.4f} ({result['pd_score']*100:.2f}%)")
        print(f"  • Risk Tier: {result['risk_tier']}")
        print(f"  • Decision: {result['decision']}")
        print(f"  • Credit Limit: ${result['credit_limit']:,}")
        print(f"  • Interest Rate: {result['interest_rate']:.2f}% APR")
        
        print(f"\nTop Contributing Factors:")
        for i, factor in enumerate(result['top_factors'][:5], 1):
            impact_direction = "increases" if factor['impact'] > 0 else "decreases"
            print(f"  {i}. {factor['feature']}: {impact_direction} risk (impact: {factor['impact']:.4f})")
        
        if result.get('adverse_action_reasons'):
            print(f"\nAdverse Action Reasons:")
            for reason in result['adverse_action_reasons']:
                print(f"  • {reason}")
        
        print(f"\nProcessing Time: {result['processing_time_ms']:.2f}ms")
        
        return True
    else:
        print(f"❌ Scoring failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False


def test_high_risk_application():
    """Test scoring a high-risk application."""
    print("\n" + "="*60)
    print("Testing High-Risk Application...")
    print("="*60)
    
    # Example application (subprime candidate)
    application = {
        "application_id": "TEST_002",
        "age": 22,
        "gender": "F",
        "income_total": 35000,
        "credit_amount": 120000,  # Much higher than income
        "annuity_amount": 5000,
        "days_employed": -180,  # Only 6 months
        "ext_source_1": 0.25,
        "ext_source_2": 0.30,
        "ext_source_3": 0.28
    }
    
    print("\nApplication Details:")
    print(f"  • Income: ${application['income_total']:,}")
    print(f"  • Credit Amount: ${application['credit_amount']:,}")
    print(f"  • Credit-to-Income Ratio: {application['credit_amount']/application['income_total']:.2f}x")
    print(f"  • Age: {application['age']}")
    print(f"  • External Score 2: {application['ext_source_2']}")
    
    response = requests.post(f"{API_URL}/score", json=application)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ Scoring Successful!")
        print(f"\nResults:")
        print(f"  • PD Score: {result['pd_score']:.4f} ({result['pd_score']*100:.2f}%)")
        print(f"  • Risk Tier: {result['risk_tier']}")
        print(f"  • Decision: {result['decision']}")
        
        if result['decision'] == 'REJECTED':
            print(f"\n❌ APPLICATION REJECTED")
            if result.get('adverse_action_reasons'):
                print(f"\nAdverse Action Reasons:")
                for reason in result['adverse_action_reasons']:
                    print(f"  • {reason}")
        
        return True
    else:
        print(f"❌ Scoring failed: {response.status_code}")
        return False


def test_batch_scoring():
    """Test batch scoring."""
    print("\n" + "="*60)
    print("Testing Batch Scoring...")
    print("="*60)
    
    applications = [
        {
            "application_id": f"BATCH_{i}",
            "age": 30 + i * 5,
            "gender": "M" if i % 2 == 0 else "F",
            "income_total": 100000 + i * 20000,
            "credit_amount": 30000 + i * 10000,
            "ext_source_2": 0.5 + i * 0.05
        }
        for i in range(3)
    ]
    
    batch_request = {"applications": applications}
    
    response = requests.post(f"{API_URL}/score/batch", json=batch_request)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Batch scored {result['batch_size']} applications")
        
        # Summary
        decisions = [r['decision'] for r in result['results']]
        approved = decisions.count('APPROVED')
        rejected = decisions.count('REJECTED')
        
        print(f"\nBatch Summary:")
        print(f"  • Approved: {approved}")
        print(f"  • Rejected: {rejected}")
        
        return True
    else:
        print(f"❌ Batch scoring failed: {response.status_code}")
        return False


def test_monitoring_stats():
    """Test monitoring stats endpoint."""
    print("\n" + "="*60)
    print("Testing Monitoring Stats...")
    print("="*60)
    
    response = requests.get(f"{API_URL}/monitoring/stats")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Total Requests: {data.get('total_requests', 0)}")
        print(f"✅ Production Batches: {data.get('production_batches', 0)}")
        
        alerts = data.get('alerts', [])
        if alerts:
            print(f"\nRecent Alerts ({len(alerts)}):")
            for alert in alerts[:5]:
                print(f"  • [{alert['type']}] {alert['message']}")
        else:
            print(f"\n✅ No alerts")
        
        return True
    else:
        print(f"❌ Monitoring stats failed: {response.status_code}")
        return False


def main():
    """Run all API tests."""
    print("\n" + "="*70)
    print("CREDIT RISK API TEST SUITE")
    print("="*70)
    print(f"\nAPI URL: {API_URL}")
    
    # Test endpoints
    tests = [
        ("Health Check", test_health),
        ("Model Info", test_model_info),
        ("Single Scoring (Prime)", test_single_scoring),
        ("Single Scoring (High Risk)", test_high_risk_application),
        ("Batch Scoring", test_batch_scoring),
        ("Monitoring Stats", test_monitoring_stats)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} raised exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
