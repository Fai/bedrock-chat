# AWS Certified Security Specialty (SCS-C02) Study Plan
## 10-12 Week Weekday-Only Study Guide

**Target Certification:** AWS Certified Security - Specialty (SCS-C02)
**Your Background:** Cloud Practitioner, AI Practitioner, Solutions Architect Associate, ML Engineer Associate
**Timeline:** 10-12 weeks (weekdays only, 3 hours/day)
**Study Time:** 6-7 AM (1h) + 8-10 PM (2h) = 3 hours/day, 15 hours/week
**Resources:** AWS Skill Builder subscription + supplementary materials

---

## Exam Overview

- **Duration:** 170 minutes
- **Questions:** 65 (50 scored, 15 unscored)
- **Passing Score:** 750/1000
- **Cost:** $300
- **Format:** Multiple choice/multiple response

### Exam Domains & Weights

| Domain | Weight | Focus |
|--------|--------|-------|
| 1. Threat Detection & Incident Response | 14% | IR plans, threat detection, compromise response |
| 2. Security Logging & Monitoring | 18% | CloudTrail, CloudWatch, log analysis |
| 3. Infrastructure Security | 20% | VPC, WAF, Shield, network controls |
| 4. Identity & Access Management | 16% | IAM, STS, Cognito, Directory Services |
| 5. Data Protection | 18% | KMS, encryption, secrets management |
| 6. Management & Security Governance | 14% | Config, Organizations, compliance |

---

## Week-by-Week Study Plan

### **Weeks 1-2: Foundation & IAM Deep Dive**
**Goal:** Establish security fundamentals and master identity services
**Time Required:** 12-15 hours (spread across 2 weeks)

#### Week 1 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | Exam Prep Course (intro modules) | IAM basics hands-on: Create users, groups, policies |
| Tue | Exam Prep Course (IAM modules) | IAM roles: EC2 instance roles, cross-account access |
| Wed | "Deep Dive into IAM" course | STS assume role scenarios + IAM Access Analyzer |
| Thu | IAM policy evaluation logic study | Permission boundaries lab |
| Fri | Review IAM documentation | 20 practice questions on IAM + review |

#### Week 2 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | AWS Organizations + SCP video | Organizations lab: Create OUs, apply SCPs |
| Tue | IAM Identity Center (SSO) course | SSO configuration lab |
| Wed | Cognito user pools study | Cognito lab: User pool + identity pool setup |
| Thu | Directory Service overview | Review all IAM concepts |
| Fri | IAM whitepaper reading | 30 practice questions (IAM + Orgs) + review |

**Key Services to Master:**
- IAM (policies, roles, conditions, permission boundaries)
- AWS STS, AWS Organizations (SCPs)
- IAM Identity Center (AWS SSO)
- Amazon Cognito, AWS Directory Service

**Study Tips:**
- Focus on IAM policy evaluation logic (explicit deny > explicit allow > implicit deny)
- Understand identity-based vs resource-based policies
- Practice writing least-privilege policies

---

### **Weeks 3-4: Data Protection & Encryption**
**Goal:** Master encryption mechanisms and data security
**Time Required:** 12-15 hours (spread across 2 weeks)

#### Week 3 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | "Data Protection on AWS" course | KMS basics: Create CMKs, key policies |
| Tue | "KMS Deep Dive" course (part 1) | KMS grants and key rotation lab |
| Wed | "KMS Deep Dive" course (part 2) | Envelope encryption implementation |
| Thu | Encryption at rest/transit study | S3 encryption lab (SSE-S3, SSE-KMS, SSE-C) |
| Fri | KMS best practices whitepaper | EBS + RDS encryption + 15 practice questions |

#### Week 4 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | AWS Secrets Manager overview | Secrets Manager lab: Store/rotate secrets |
| Tue | Parameter Store study | Parameter Store vs Secrets Manager comparison lab |
| Wed | AWS Certificate Manager (ACM) | ACM lab: SSL/TLS certificates |
| Thu | CloudHSM vs KMS study | Macie for data discovery lab |
| Fri | Review all encryption concepts | 30 practice questions (KMS, encryption) + review |

**Key Services to Master:**
- AWS KMS (CMK types, key policies, grants, rotation)
- AWS Secrets Manager, Parameter Store
- AWS Certificate Manager (ACM)
- AWS CloudHSM, Macie

**Study Tips:**
- KMS vs CloudHSM: KMS for most cases, CloudHSM for compliance (FIPS 140-2 Level 3)
- Key rotation: Automatic (yearly) vs manual
- Know encryption for S3, EBS, RDS, EFS, etc.

---

### **Weeks 5-6: Infrastructure Security**
**Goal:** Master network security and edge protection
**Time Required:** 12-15 hours (spread across 2 weeks)

#### Week 5 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | "Advanced VPC Security" course | VPC lab: Security groups vs NACLs |
| Tue | "AWS Network Security" course | VPC endpoints: Gateway vs Interface |
| Wed | VPC Flow Logs study | VPC Flow Logs lab + analysis |
| Thu | PrivateLink overview | PrivateLink lab for service connections |
| Fri | VPC security whitepaper | 20 practice questions on VPC security |

#### Week 6 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | AWS WAF overview | WAF lab: Create rules, rate limiting |
| Tue | Shield Standard vs Advanced | Network Firewall lab |
| Wed | CloudFront security study | CloudFront: Signed URLs, OAI/OAC lab |
| Thu | Route 53 (DNSSEC, Resolver) | Transit Gateway + VPN security |
| Fri | Review all network security | 30 practice questions (infra security) + review |

**Key Services to Master:**
- VPC (security groups, NACLs, VPC endpoints, Flow Logs)
- AWS WAF & Shield
- Network Firewall
- Transit Gateway, PrivateLink
- Route 53 (DNSSEC, Resolver)
- CloudFront (signed URLs, OAI/OAC)

**Study Tips:**
- Security Groups = stateful, NACLs = stateless
- Gateway endpoints (S3, DynamoDB) vs Interface endpoints (everything else)
- WAF: Rate-based rules, geo-blocking, managed rule groups

---

### **Weeks 7-8: Logging & Monitoring**
**Goal:** Implement comprehensive security monitoring
**Time Required:** 12-15 hours (spread across 2 weeks)

#### Week 7 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | "Security Logging and Monitoring" course | CloudTrail basics: Enable organization trails |
| Tue | "CloudTrail Deep Dive" course | CloudTrail Insights + log file validation |
| Wed | CloudWatch Logs study | CloudWatch Logs: Metric filters, alarms |
| Thu | CloudWatch metrics & alarms | Create security event alarms lab |
| Fri | Log aggregation strategies | 20 practice questions on CloudTrail/CloudWatch |

#### Week 8 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | AWS Config overview | Config rules lab: Compliance tracking |
| Tue | EventBridge for security | EventBridge: Automate security responses |
| Wed | VPC Flow Logs deep dive | S3 + ELB access logs analysis |
| Thu | "Troubleshooting: Security Logging" | Custom Config rules lab |
| Fri | Review all logging concepts | 30 practice questions (logging/monitoring) + review |

**Key Services to Master:**
- CloudTrail (organization trails, Insights, validation)
- CloudWatch (Logs, Metrics, Alarms, metric filters)
- EventBridge (event-driven automation)
- AWS Config (rules, compliance)
- VPC Flow Logs, S3 Access Logs, ELB Access Logs

**Study Tips:**
- CloudTrail = API call logging, CloudWatch = monitoring/metrics
- Log retention: CloudWatch (indefinite), S3 (lifecycle policies)
- EventBridge patterns for security automation

---

### **Weeks 9-10: Threat Detection & Incident Response**
**Goal:** Detect threats and respond to incidents
**Time Required:** 12-15 hours (spread across 2 weeks)

#### Week 9 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | "Incident Detection and Response" course | GuardDuty: Enable and explore findings |
| Tue | "GuardDuty Deep Dive" course | GuardDuty finding types study + suppression rules |
| Wed | Security Hub overview | Security Hub lab: Aggregate findings |
| Thu | Detective for investigation | Detective lab: Analyze security events |
| Fri | GuardDuty best practices | 20 practice questions on threat detection |

#### Week 10 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | Amazon Inspector overview | Inspector: Vulnerability scanning lab |
| Tue | "Security Automation on AWS" course | Lambda for IR automation lab |
| Wed | Incident response procedures | Forensic snapshot creation lab |
| Thu | Systems Manager Incident Manager | IR automation workflows |
| Fri | Review all threat detection | 30 practice questions (IR + detection) + review |

**Key Services to Master:**
- Amazon GuardDuty (finding types, suppression)
- AWS Security Hub (aggregation, insights)
- Amazon Detective (investigation graphs)
- Amazon Inspector (vulnerability scanning)
- Systems Manager (Incident Manager)
- AWS Lambda (IR automation)

**Study Tips:**
- GuardDuty finding types: Reconnaissance, Instance compromise, Account compromise
- Automated IR: GuardDuty → EventBridge → Lambda → remediation
- Forensics: Create snapshots, isolate instances, preserve evidence

---

### **Week 11: Management & Governance**
**Goal:** Implement governance and compliance controls
**Time Required:** 12-15 hours (spread across 1 week)

#### Week 11 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | "AWS Security Governance at Scale" | Review Organizations + advanced SCP patterns |
| Tue | "Compliance and Governance on AWS" | Config for compliance tracking lab |
| Wed | "Control Tower and Landing Zones" | Control Tower setup (if available) |
| Thu | Audit Manager overview | Systems Manager: Patch/Session Manager lab |
| Fri | AWS Artifact + compliance docs | 30 practice questions (governance) + review |

**Key Services to Master:**
- AWS Organizations (SCPs, OUs, tag policies)
- AWS Control Tower (guardrails, Account Factory)
- AWS Config (conformance packs)
- AWS Audit Manager
- Systems Manager (Patch Manager, Session Manager)
- AWS Artifact

**Study Tips:**
- SCP evaluation: Most restrictive policy wins
- Control Tower guardrails: Preventive (SCPs) vs Detective (Config)
- Compliance frameworks: PCI-DSS, HIPAA, GDPR, SOC 2

---

### **Week 12: Practice Exams & Weak Areas**
**Goal:** Identify and strengthen weak areas
**Time Required:** Full week of intensive practice

#### Week 12 Daily Schedule
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | AWS Official Practice Question Set (half) | Review answers + study weak topics |
| Tue | AWS Official Practice Question Set (half) | Review answers + flashcards |
| Wed | Tutorials Dojo Practice Exam 1 (timed) | Review all incorrect answers deeply |
| Thu | Study weak areas from Exam 1 | Hands-on labs for weak services |
| Fri | Tutorials Dojo Practice Exam 2 (timed) | Review all incorrect answers + notes |

**Focus Areas:**
- Aim for 80%+ scores
- Track recurring weak topics
- Time yourself: 170 min / 65 questions = 2.6 min/question
- Flag questions for review

**Study Strategy:**
- Review incorrect answers thoroughly
- Understand WHY wrong answers are wrong
- Create summary notes for weak areas

---

### **Week 13: Final Review & Exam**
**Goal:** Consolidate knowledge and take the exam

#### Days 1-3: Comprehensive Review
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Mon | Review Domains 1-2 (IR + Logging) | Re-do flagged questions from practice exams |
| Tue | Review Domains 3-4 (Infrastructure + IAM) | AWS Security Best Practices whitepaper |
| Wed | Review Domains 5-6 (Data + Governance) | Well-Architected Security Pillar whitepaper |

#### Days 4-5: Final Practice
| Day | Morning (6-7 AM) | Evening (8-10 PM) |
|-----|------------------|-------------------|
| Thu | Review weak topics | Tutorials Dojo Practice Exam 3 (timed, aim 85%+) |
| Fri | KMS + IAM whitepapers | Review Exam 3 answers + create cheat sheet |

#### Day 6: Light Review
- **Morning:** Review cheat sheets and flashcards
- **Evening:** Quick scan of key services (no heavy study)
- Get good sleep - rest your brain!

#### Day 7: Exam Day
- Schedule exam for afternoon (after work if possible)
- Light review in morning - don't cram
- **During exam:**
  - Read questions carefully
  - Flag uncertain questions
  - Eliminate obviously wrong answers
  - Stay calm and confident

---

## Daily Study Schedule (Customized for Your Availability)

**Available Time:**
- 6:00-7:00 AM (1 hour)
- 8:00-10:00 PM (2 hours)
- **Total: 3 hours/weekday**
- **Weekends: Reserved for housework**

**Study Approach:** Extended 10-12 week timeline to accommodate weekday-only study

### Weekday Schedule (Monday-Friday)

**Morning Session (6:00-7:00 AM) - 1 hour:**
- Theory/Video learning ONLY
- Watch AWS Skill Builder courses
- Read documentation/whitepapers
- Review flashcards and study notes
- *Why morning?* Passive learning when you're fresh but may be groggy

**Evening Session (8:00-10:00 PM) - 2 hours:**
- **8:00-9:00 PM:** Hands-on labs (AWS Console practice)
- **9:00-10:00 PM:** Practice questions + review incorrect answers
- *Why evening?* Active learning when you're fully alert

**Total Weekday Study:** 15 hours/week (3 hours × 5 days)

### Study Strategy

Given 15 hours/week (vs original 20-25 hours/week), the plan extends to **10-12 weeks** instead of 8 weeks to maintain quality without burnout.

---

## Key Resources

### AWS Skill Builder (Your Subscription)
✅ Exam Prep Standard Course: AWS Certified Security - Specialty
✅ AWS Builder Labs (hands-on practice)
✅ AWS Cloud Quest (gamified learning)
✅ Official Practice Question Set
✅ All domain-specific courses listed above

### Recommended Supplementary Resources
- **Practice Exams:** Tutorials Dojo AWS Security Specialty Practice Exams (highly recommended)
- **Video Course:** Stephane Maarek's "Ultimate AWS Certified Security Specialty" on Udemy (optional, complements Skill Builder)
- **Documentation:** AWS Security Documentation and Whitepapers
- **Community:** AWS re:Post, Reddit r/AWSCertifications

### Essential AWS Whitepapers
1. AWS Security Best Practices
2. AWS Well-Architected Framework - Security Pillar
3. AWS KMS Best Practices
4. IAM Best Practices
5. Overview of AWS Security - Data Protection

---

## Critical Services to Know Inside-Out

### Tier 1 (Master These):
- IAM (policies, roles, conditions, boundaries)
- KMS (keys, policies, grants, rotation)
- VPC (security groups, NACLs, endpoints)
- CloudTrail (organization trails, log validation)
- GuardDuty (findings, response)
- AWS WAF & Shield
- Secrets Manager
- AWS Config

### Tier 2 (Strong Understanding):
- Security Hub
- Detective
- Inspector
- Macie
- Organizations (SCPs)
- Systems Manager
- CloudWatch (logs, metrics)
- ACM, CloudHSM
- Cognito

### Tier 3 (Basic Understanding):
- Control Tower
- Audit Manager
- Network Firewall
- Directory Service
- RAM (Resource Access Manager)
- Artifact

---

## Exam Day Tips

1. **Time Management:** You have ~2.6 minutes per question. Don't get stuck.
2. **Flag Questions:** Mark uncertain ones and come back after finishing all questions.
3. **Eliminate Wrong Answers:** Usually 1-2 options are obviously wrong.
4. **Look for Keywords:** "Most cost-effective," "least operational overhead," "most secure"
5. **Scenario-Based:** Most questions are scenario-based, so understand the use case.
6. **Service Integration:** Know how services work together (e.g., GuardDuty → EventBridge → Lambda).
7. **Read Carefully:** AWS loves subtle differences in answer options.

---

## Weekly Progress Checklist

### Weeks 1-2: ☐ IAM fundamentals ☐ Organizations ☐ STS ☐ Cognito ☐ Directory Service ☐ SCPs

### Weeks 3-4: ☐ KMS ☐ CloudHSM ☐ Secrets Manager ☐ ACM ☐ Macie ☐ Encryption mastery

### Weeks 5-6: ☐ VPC security ☐ WAF ☐ Shield ☐ Network Firewall ☐ CloudFront ☐ Route 53

### Weeks 7-8: ☐ CloudTrail ☐ CloudWatch ☐ VPC Flow Logs ☐ Config ☐ EventBridge

### Weeks 9-10: ☐ GuardDuty ☐ Security Hub ☐ Detective ☐ Inspector ☐ IR automation

### Week 11: ☐ Organizations deep dive ☐ Control Tower ☐ Compliance frameworks ☐ Audit Manager

### Week 12: ☐ Practice exam 1 ☐ Practice exam 2 ☐ Practice exam 3 ☐ Weak area review

### Week 13: ☐ Final review ☐ Whitepapers ☐ Final practice ☐ Schedule exam ☐ Pass exam!

---

## Success Indicators

**You're ready for the exam when you can:**
- Consistently score 85%+ on practice exams
- Explain the difference between IAM policy types without hesitation
- Design a secure multi-account architecture
- Choose the right encryption service for any scenario
- Troubleshoot security logging issues
- Recommend incident response workflows
- Understand all GuardDuty finding types

---

## Notes for Your Background

Given your existing certifications:
- **✅ Strength:** You already understand AWS fundamentals and architecture patterns
- **✅ Strength:** Your SAA knowledge gives you a solid VPC and IAM foundation
- **🎯 Focus:** Deep dive into security-specific services (GuardDuty, Security Hub, Macie, Inspector)
- **🎯 Focus:** Advanced IAM scenarios (permission boundaries, session policies, SCPs)
- **🎯 Focus:** Encryption mechanisms and key management strategies

You're well-positioned for this exam. The security specialty builds on SAA knowledge but requires deep expertise in security services and incident response.

---

## Motivation

The AWS Security Specialty is one of the highest-paying AWS certifications and demonstrates expert-level security knowledge. With your existing certifications and a focused 13-week weekday-only plan, you're set up for success!

---

## Study Plan Summary

**Timeline:** 13 weeks (65 weekdays)
**Daily Commitment:** 3 hours/day (6-7 AM + 8-10 PM)
**Total Study Hours:** ~195 hours (65 days × 3 hours)
**Weekends:** Free for housework and rest

**Study Breakdown:**
- **Weeks 1-2:** IAM & Identity (Foundation)
- **Weeks 3-4:** Data Protection & Encryption
- **Weeks 5-6:** Infrastructure Security
- **Weeks 7-8:** Logging & Monitoring
- **Weeks 9-10:** Threat Detection & Incident Response
- **Week 11:** Management & Governance
- **Week 12:** Intensive Practice Exams
- **Week 13:** Final Review & Exam

**Morning Sessions (6-7 AM):**
- Video courses
- Documentation reading
- Theoretical study
- Whitepapers

**Evening Sessions (8-10 PM):**
- Hands-on labs (1 hour)
- Practice questions + review (1 hour)
- Skill application

**Success Formula:**
1. Consistency > intensity (3 hours daily beats cramming)
2. Hands-on practice every evening
3. Practice questions from day 1
4. Review incorrect answers thoroughly
5. Weekday-only = sustainable without burnout

**Target Exam Date:** Week 13, Day 7 (Schedule 2-3 weeks in advance)

**Good luck! You've got this! 🚀**
