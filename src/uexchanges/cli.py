from __future__ import annotations
import json,sys
from datetime import date,datetime,timedelta,timezone
from .eligibility import evaluate_eligibility
from .models import ApplicantProfile,Opportunity,Role
from .scoring import DEFAULT_WEIGHTS,score_opportunity

def demo()->int:
    profile=ApplicantProfile(residence_country="ES",age=24,languages={"English","Spanish"},available_from=date.today(),available_to=date.today()+timedelta(days=365))
    opp=Opportunity(opportunity_id="demo",title="Demo Youth Worker Training",programme="Erasmus+ Youth Workers",role=Role.YOUTH_WORKER,source_url="https://example.invalid/demo",deadline=datetime.now(timezone.utc)+timedelta(days=14),start_date=date.today()+timedelta(days=30),end_date=date.today()+timedelta(days=36),eligible_countries={"ES","PT","IT"},age_min=18,required_languages={"English"})
    eligibility=evaluate_eligibility(profile,opp); score=score_opportunity(eligibility,{k:0.8 for k in DEFAULT_WEIGHTS})
    print(json.dumps({"eligibility":eligibility.result.value,"score":score.total,"band":score.band},indent=2)); return 0

def main()->int:
    if len(sys.argv)>=2 and sys.argv[1]=="demo": return demo()
    print("Usage: python -m uexchanges.cli demo"); return 2
if __name__=="__main__": raise SystemExit(main())
