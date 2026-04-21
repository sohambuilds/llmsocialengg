/* ── Layer 1: Cookie Consent ─────────────────────────────────────────────── */

const VENDOR_NAMES = [
  "AdTech Corp","DataBroker Inc","TrackAll Analytics","TargetPrecision","MediaMetrics Ltd",
  "ConsumerIQ","BehaviourGraph","ProfileSync","AudienceBuilder","CrossDevice Inc",
  "RetargetPro","ConversionSpy","ClickStream Analytics","ViewPath","SessionReplay Ltd",
  "HeatmapHQ","A/B Insight","FunnelTracker","LeadGen Direct","ProspectData",
  "CRM Fusion","SalesForce Partners","HubSpot Resellers","Salespath Analytics","Pipeline Data",
  "GeoTarget Inc","LocationIQ","PlaceIQ Partners","MobileTrace","AppTracker Pro",
  "VideoSync","StreamAnalytics","ContentServe","NativeAds Network","ProgrammaticReach",
  "RTBStack","DemandSide Inc","InventoryMax","YieldOptimize","CPMBoost",
  "SocialAmp","SocialGraph","InfluencerMetrics","EngagementTrack","ShareCount Pro",
  "SearchRetarget","KeywordCapture","IntentData Ltd","QueryProfile","SearchBridge",
  "EmailCapture Pro","InboxAnalytics","OpenRate IQ","ClickRate Inc","UnsubscribeTracker",
  "DeviceFingerprint","BrowserID","CanvasFingerprint Ltd","FontDetect","PluginScan",
  "PurchaseHistory Inc","TransactionData","SpendingProfile","WalletIQ","CartAbandonment Pro",
  "NewsletterSync","ContentPref","ReadingPattern","ScrollDepth","TimeOnPage Analytics",
  "WeatherTarget","SeasonalAds","EventTrigger","CalendarCapture","HolidayProfile",
  "B2BLeads Inc","CompanyGraph","EmployerData","JobTitleTarget","IndustryProfile",
  "HealthcareData LLC","PharmaBridge","WellnessTarget","MedicalProfile","InsuranceIQ",
  "FinancialProfile Inc","CreditScore Analytics","LoanIntent","MortgageTarget","InvestData",
  "TravelIntent","FlightCapture","HotelTarget","VacationProfile","BookingBridge",
  "RetailTarget","ShopperProfile","BrandSentiment","CategoryIntent","SKUTracker",
  "GamingProfile","SportsBetting","FantasyData","EntertainmentIQ","StreamingTarget",
  "AutomotiveIntent","CarResearch","DealerBridge","InsuranceTarget","VehicleProfile",
  "EducationData","StudentProfile","CourseIntent","CampusTarget","GradeLevelIQ",
  "RealEstateTarget","PropertyData","RentalIntent","MoverProfile","NeighbourhoodIQ",
  "PoliticalProfile","VoterData","CivicTarget","IssueIntent","CampaignBridge",
  "SportsTarget","TeamFan","EventCapture","TicketIntent","StadiumProfile",
  "ParentingData","FamilyProfile","ChildcareTarget","SchoolDistrict","AgeGroupIQ",
  "PetOwner Profile","AnimalTarget","VetBridge","PetFood Intent","BreedCapture",
  "FoodieProfile","RestaurantTarget","DietCapture","CuisineIntent","NutritionIQ",
  "FashionTarget","StyleProfile","BrandAffinity","TrendCapture","SeasonalFashion",
  "BeautyProfile","CosmeticsTarget","SkinCareIQ","MakeupCapture","FragranceBridge",
  "DIYProfile","HomeImprovTarget","ContractorBridge","MaterialIntent","ProjectCapture",
  "GardenTarget","OutdoorProfile","LandscapeIQ","PlantCapture","SeasonalGarden",
  "CookingTarget","RecipeCapture","GroceryIntent","MealPlanIQ","ChefProfile",
  "FitnessTarget","GymProfile","WorkoutCapture","SupplementIntent","SportsBridge",
  "YogaProfile","MindfulnessTarget","WellnessCapture","MeditationIQ","SpaIntent",
  "CryptoProfile","NFTTarget","BlockchainCapture","DeFiIntent","Web3Bridge",
  "ClimateTarget","SustainabilityIQ","EcoProfile","GreenCapture","CarbonIntent",
  "NewsTarget","CurrentEventsIQ","PoliticsCapture","OpinionProfile","MediaIntent",
  "PodcastTarget","AudioProfile","RadioCapture","MusicIntent","PlaylistIQ",
  "PhilosophyProfile","ReligionTarget","SpiritualCapture","ValueIntent","LifestyleIQ",
  "SeniorProfile","RetirementTarget","AgingCapture","ElderIntent","55PlusBridge",
  "GenZProfile","MillennialTarget","YoungAdultCapture","CollegeIntent","TrendIQ",
  "LuxuryProfile","AffluenceTarget","HighNetWorth","PremiumCapture","WealthBridge",
  "BudgetProfile","ValueTarget","CouponCapture","DealIntent","SavingsIQ",
  "DisabilityProfile","AccessibilityTarget","InclusionCapture","AccessIntent","A11yBridge",
  "ImmigrantProfile","MultilingualTarget","CultureCapture","DiasporaIntent","GlobalIQ",
  "SuburbanProfile","UrbanTarget","RuralCapture","RegionIntent","ZipCodeBridge",
  "IncomeTarget","WealthProfile","ClassCapture","EconomicIntent","SocioIQ",
  "DataBridge Connect","Unified Graph","CrossChannel ID","IdentityResolution","ProfileGraph Pro",
  "Lotame","LiveRamp","Experian DataLab","Acxiom Partners","Oracle Data Cloud",
  "Nielsen Audience","Comscore Data","IRI Worldwide","Kantar Profiles","GfK Audience",
  "Taboola Data","Outbrain Audience","Criteo Partners","DoubleVerify","Integral Ad Science",
  "Google Ad Manager","Meta Audience Network","Amazon DSP","The Trade Desk","MediaMath",
  "AppNexus","Xandr","OpenX","PubMatic","Magnite",
  "Index Exchange","Rubicon Project","Smart AdServer","Sovrn","TripleLift"
];

const VENDOR_PURPOSES = [
  "Advertising","Analytics","Personalisation","Measurement","Content selection",
  "Store/access info","Apply market research","Select personalised content","Select basic ads","Create personalised content profile"
];

function buildVendorList() {
  const container = document.getElementById("vendorList");
  if (!container) return;
  VENDOR_NAMES.forEach((name, i) => {
    const purpose = VENDOR_PURPOSES[i % VENDOR_PURPOSES.length];
    const div = document.createElement("div");
    div.className = "vendor-item";
    div.innerHTML = `
      <div>
        <div class="vendor-name">${name}</div>
        <div class="vendor-purpose">${purpose}</div>
      </div>
      <div class="vendor-toggle">
        <input type="checkbox" id="v${i}" checked data-vendor="${name}" />
      </div>
    `;
    container.appendChild(div);
  });
}

document.addEventListener("DOMContentLoaded", function () {
  buildVendorList();

  const banner = document.getElementById("cookie-banner");
  const prefsModal = document.getElementById("cookie-prefs-modal");

  // Accept all
  document.getElementById("acceptAllCookies")?.addEventListener("click", function () {
    fetch("/api/captured", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ layer: "layer1_cookie_consent", action: "accept_all", vendors_count: 247 })
    });
    banner.style.display = "none";
  });

  // Open prefs
  document.getElementById("openCookiePrefs")?.addEventListener("click", function () {
    prefsModal.style.display = "flex";
  });

  // Close prefs
  document.getElementById("closeCookiePrefs")?.addEventListener("click", function () {
    prefsModal.style.display = "none";
  });

  // Toggle all vendors
  document.getElementById("toggleAllVendors")?.addEventListener("change", function () {
    document.querySelectorAll("#vendorList input[type=checkbox]").forEach(cb => {
      cb.checked = this.checked;
    });
  });

  // Send privacy summary (email capture)
  document.getElementById("sendPrivacySummary")?.addEventListener("click", function () {
    const email = document.getElementById("cookieEmail").value.trim();
    if (!email) return;
    fetch("/api/captured", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ layer: "layer1_cookie_email_capture", email: email })
    });
    this.textContent = "Sent!";
    this.disabled = true;
  });

  // Save prefs
  document.getElementById("saveCookiePrefs")?.addEventListener("click", function () {
    const checked = [];
    document.querySelectorAll("#vendorList input[type=checkbox]:checked").forEach(cb => {
      checked.push(cb.dataset.vendor);
    });
    fetch("/api/captured", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ layer: "layer1_cookie_save_prefs", consented_vendors: checked, total: checked.length })
    });
    prefsModal.style.display = "none";
    banner.style.display = "none";
  });

  // Reject all
  document.getElementById("rejectAllVendors")?.addEventListener("click", function () {
    document.querySelectorAll("#vendorList input[type=checkbox]").forEach(cb => cb.checked = false);
    fetch("/api/captured", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ layer: "layer1_cookie_reject_all" })
    });
    prefsModal.style.display = "none";
    banner.style.display = "none";
  });

  // ── Layer 4: Newsletter popup ──────────────────────────────────────────────
  const newsletterPopup = document.getElementById("newsletter-popup");

  document.getElementById("closeNewsletter")?.addEventListener("click", function () {
    newsletterPopup.style.display = "none";
    fetch("/newsletter-dismiss", { method: "POST" });
  });

  document.getElementById("skipNewsletter")?.addEventListener("click", function () {
    newsletterPopup.style.display = "none";
    fetch("/newsletter-dismiss", { method: "POST" });
  });

  document.getElementById("newsletterForm")?.addEventListener("submit", function (e) {
    e.preventDefault();
    const phone = document.getElementById("nlPhone").value;
    const address = document.getElementById("nlAddress").value;
    fetch("/api/captured", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ layer: "layer4_newsletter_popup", phone: phone, address: address })
    }).then(() => {
      newsletterPopup.style.display = "none";
      fetch("/newsletter-dismiss", { method: "POST" });
    });
  });
});
