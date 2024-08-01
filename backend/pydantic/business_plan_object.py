from typing import List, Dict, Any
from langchain_core.pydantic_v1 import BaseModel, Field

class ExecutiveSummary(BaseModel):
    BusinessName: str = Field(description="The name of the business")
    BusinessLocation: str = Field(description="The location of the business")
    BusinessDescription: str = Field(description="A description of the business")
    MissionStatement: str = Field(description="The mission statement of the business")
    BusinessObjectives: List[str] = Field(description="Objectives of the business")
    KeysToSuccess: List[str] = Field(description="Keys to success for the business")

class CompanyDescription(BaseModel):
    CompanyName: str = Field(description="The name of the company")
    BusinessStructure: str = Field(description="The business structure")
    BusinessOwner: str = Field(description="The owner of the business")
    CompanyHistory: str = Field(description="The history of the company")
    CompanyLocation: str = Field(description="The location of the company")
    CompanyGoals: List[str] = Field(description="Goals of the company")

class ProductsAndServices(BaseModel):
    ProductOrService: str = Field(description="The product or service offered")
    ProductDescription: str = Field(description="A description of the product or service")
    CompetitiveAdvantages: List[str] = Field(description="Competitive advantages")
    PricingStructure: str = Field(description="The pricing structure")
    ProductLifecycle: str = Field(description="The product lifecycle")
    ResearchAndDevelopment: str = Field(description="Research and development details")
    IntellectualProperty: str = Field(description="Intellectual property details")

class MarketSegment(BaseModel):
    MarketSegment: str = Field(description="Market segment")
    MarketNeeds: str = Field(description="Market needs")
    MarketTrends: str = Field(description="Market trends")
    MarketGrowth: str = Field(description="Market growth")

class CompetitiveAnalysis(BaseModel):
    Competitors: List[str] = Field(description="List of competitors")
    CompetitorStrengths: List[str] = Field(description="Strengths of competitors")
    CompetitorWeaknesses: List[str] = Field(description="Weaknesses of competitors")

class MarketAnalysis(BaseModel):
    IndustryDescriptionAndOutlook: str = Field(description="Industry description and outlook")
    TargetMarket: MarketSegment = Field(description="Target market details")
    CompetitiveAnalysis: CompetitiveAnalysis = Field(description="Competitive analysis")
    RegulatoryRequirements: str = Field(description="Regulatory requirements")

class MarketingAndSales(BaseModel):
    MarketingStrategy: str = Field(description="Marketing strategy")
    SalesStrategy: str = Field(description="Sales strategy")
    SalesForecast: str = Field(description="Sales forecast")
    Advertising: str = Field(description="Advertising details")
    Promotions: str = Field(description="Promotions details")
    PublicRelations: str = Field(description="Public relations details")
    SalesPrograms: List[str] = Field(description="Sales programs")

class OperationsPlan(BaseModel):
    BusinessLocation: str = Field(description="Business location")
    FacilityRequirements: str = Field(description="Facility requirements")
    TechnologyRequirements: str = Field(description="Technology requirements")
    EquipmentRequirements: str = Field(description="Equipment requirements")
    InventoryManagement: str = Field(description="Inventory management details")
    SupplyChainManagement: str = Field(description="Supply chain management details")
    ProductionPlan: str = Field(description="Production plan")
    DistributionPlan: str = Field(description="Distribution plan")
    OrderFulfillment: str = Field(description="Order fulfillment details")

class ManagementAndOrganization(BaseModel):
    OrganizationalStructure: str = Field(description="Organizational structure")
    ManagementTeam: List[str] = Field(description="Management team members")
    ManagementTeamRoles: List[str] = Field(description="Roles of management team members")
    BoardOfDirectors: List[str] = Field(description="Board of directors members")
    Advisors: List[str] = Field(description="Advisors")

class StartupCosts(BaseModel):
    CostItem: str = Field(description="Startup cost item")
    Amount: str = Field(description="Amount of the startup cost")

class FundingRequirements(BaseModel):
    FundingNeeded: str = Field(description="Funding needed")
    FundingPurpose: str = Field(description="Purpose of the funding")

class RevenueProjections(BaseModel):
    RevenueStream: str = Field(description="Revenue stream")
    Amount: str = Field(description="Amount of revenue")

class ExpenseProjections(BaseModel):
    ExpenseItem: str = Field(description="Expense item")
    Amount: str = Field(description="Amount of the expense")

class ProfitAndLossStatement(BaseModel):
    Revenue: str = Field(description="Revenue")
    Expenses: str = Field(description="Expenses")
    NetProfit: str = Field(description="Net profit")

class CashFlowStatement(BaseModel):
    CashInflow: str = Field(description="Cash inflow")
    CashOutflow: str = Field(description="Cash outflow")
    NetCashFlow: str = Field(description="Net cash flow")

class BalanceSheet(BaseModel):
    Assets: str = Field(description="Assets")
    Liabilities: str = Field(description="Liabilities")
    Equity: str = Field(description="Equity")

class FinancialPlan(BaseModel):
    StartupCosts: StartupCosts = Field(description="Startup costs")
    FundingRequirements: FundingRequirements = Field(description="Funding requirements")
    RevenueProjections: RevenueProjections = Field(description="Revenue projections")
    ExpenseProjections: ExpenseProjections = Field(description="Expense projections")
    ProfitAndLossStatement: ProfitAndLossStatement = Field(description="Profit and loss statement")
    CashFlowStatement: CashFlowStatement = Field(description="Cash flow statement")
    BalanceSheet: BalanceSheet = Field(description="Balance sheet")
    BreakEvenAnalysis: str = Field(description="Break-even analysis")
    FinancialAssumptions: str = Field(description="Financial assumptions")

class Appendix(BaseModel):
    Resumes: List[str] = Field(description="Resumes")
    PermitsAndLicenses: List[str] = Field(description="Permits and licenses")
    LeaseAgreements: List[str] = Field(description="Lease agreements")
    LegalDocuments: List[str] = Field(description="Legal documents")
    OtherRelevantDocuments: List[str] = Field(description="Other relevant documents")

class BusinessModel(BaseModel):
    ExecutiveSummary: ExecutiveSummary = Field(description="Executive summary")
    CompanyDescription: CompanyDescription = Field(description="Company description")
    ProductsAndServices: ProductsAndServices = Field(description="Products and services")
    MarketAnalysis: MarketAnalysis = Field(description="Market analysis")
    MarketingAndSales: MarketingAndSales = Field(description="Marketing and sales")
    OperationsPlan: OperationsPlan = Field(description="Operations plan")
    ManagementAndOrganization: ManagementAndOrganization = Field(description="Management and organization")
    FinancialPlan: FinancialPlan = Field(description="Financial plan")
    Appendix: Appendix = Field(description="Appendix")
