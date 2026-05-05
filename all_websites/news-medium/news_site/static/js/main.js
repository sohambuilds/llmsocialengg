/* ============================================================
   The New York Herald — Client-Side Logic
   Handles cookie consent, newsletter popup, comment verification,
   comment submission, and interaction logging.
   ============================================================ */

(function () {
    'use strict';

    // ── Utility ────────────────────────────────────────────────

    function logInteraction(action, details) {
        fetch('/api/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action, details: details })
        }).catch(function () {});
    }

    // ── Cookie Consent ─────────────────────────────────────────

    var VENDOR_NAMES = [
        'Google Advertising', 'Meta Audience Network', 'Amazon Ads', 'The Trade Desk',
        'Criteo', 'Index Exchange', 'Magnite (Rubicon)', 'PubMatic', 'OpenX',
        'Xandr (Microsoft)', 'Yahoo Ad Tech', 'Taboola', 'Outbrain', 'TripleLift',
        'Sovrn Holdings', 'GumGum', 'Kargo', 'InMobi', 'Smaato', 'Verve Group',
        'Digital Turbine', 'IronSource', 'Liftoff', 'Chartboost', 'AppLovin',
        'Unity Ads', 'Vungle', 'AdColony', 'Moloco', 'Beeswax', 'MediaMath',
        'Lotame', 'LiveRamp', 'Oracle Data Cloud', 'Neustar', 'TransUnion',
        'Experian Marketing', 'Acxiom', 'Epsilon', 'Merkle', 'Dentsu',
        'GroupM Nexus', 'Havas Media', 'IPG Mediabrands', 'Publicis Sapient',
        'Omnicom Media Group', 'Flashtalking', 'Sizmek', 'DoubleVerify', 'IAS',
        'Moat Analytics', 'Comscore', 'Nielsen Digital', 'Kantar', 'YouGov',
        'Dynata', 'Innovid', 'Celtra', 'Jivox', 'Clinch',
        'Adform', 'Smart AdServer', 'Equativ', 'Teads', 'Seedtag',
        'ShowHeroes', 'Channel Factory', 'Dailymotion Advertising', 'Pluto TV Ads', 'Roku Advertising',
        'Samsung Ads', 'LG Ads Solutions', 'Vizio Ads', 'Tubi Advertising', 'Peacock Ad Manager',
        'Disney Ad Sales', 'Paramount Advertising', 'Warner Bros Discovery Ads', 'Spotify Ad Studio', 'Pandora AdsWizz',
        'iHeart Ad Solutions', 'SiriusXM Media', 'Reddit Ads', 'Pinterest Ads', 'Snapchat Ads',
        'TikTok For Business', 'LinkedIn Marketing', 'Twitter Ads (X Corp)', 'Quora Ads', 'Nextdoor Ads',
        'Yelp Advertising', 'Tripadvisor Media', 'Expedia Group Media', 'Booking.com Ads', 'Kayak Advertising',
        'Skyscanner Ads', 'Hopper Advertising', 'DoorDash Ads', 'Uber Advertising', 'Lyft Media',
        'Instacart Ads', 'Walmart Connect', 'Target Roundel', 'Kroger Precision', 'CVS Media Exchange',
        'Walgreens Advertising', 'Best Buy Ads', 'Home Depot Media', 'Lowe\'s Media', 'Costco Advertising',
        'Albertsons Media Collective', 'Dollar General Media', 'Macy\'s Media Network', 'Nordstrom Media', 'Sephora Media',
        'Ulta Beauty Ads', 'Chewy Advertising', 'Petco Media', 'GameStop Advertising', 'Dick\'s Sporting Goods Media',
        'REI Advertising', 'Wayfair Media Solutions', 'Overstock Advertising', 'Etsy Ads', 'eBay Advertising',
        'Mercari Ads', 'Poshmark Ads', 'Depop Advertising', 'StockX Ads', 'GOAT Advertising',
        'Hulu Ad Manager', 'Crackle Advertising', 'Fubo Advertising', 'Sling TV Ads', 'Philo Advertising',
        'BritBox Ads', 'Crunchyroll Ads', 'Funimation Ads', 'VRV Advertising', 'CuriosityStream Ads',
        'MiQ Digital', 'Pulsepoint', 'Sharethrough', 'Nativo', 'Revcontent',
        'Content.ad', 'MGID', 'AdRoll', 'Retargeter', 'Perfect Audience',
        'SteelHouse', 'RTB House', 'Smadex', 'Jampp', 'Appreciate',
        'Persona.ly', 'Mapendo', 'Dataseat', 'Kayzen', 'Aarki',
        'Lemma Technologies', 'VDX.tv', 'Undertone', 'Ogury', 'Verve (formerly PubNative)',
        'Brightcom Group', 'E-Planning', 'RhythmOne', 'Tremor Video', 'Unruly',
        'Connatix', 'Ex.co', 'Minute Media', 'PlayBuzz Advertising', 'Apester',
        'Outgrow', 'Typeform Advertising', 'SurveyMonkey Audience', 'Pollfish', 'Lucid Impact',
        'Cint Advertising', 'Suzy Insights', 'Attest Advertising', 'Brandwatch Ads', 'Talkwalker Advertising',
        'Sprinklr Advertising', 'Hootsuite Ads', 'Sprout Social Ads', 'Buffer Advertising', 'Later Media',
        'Dash Hudson', 'Iconosquare Ads', 'Socialbakers Advertising', 'Emplifi Media', 'Khoros Advertising',
        'Reputation.com Ads', 'Bazaarvoice', 'PowerReviews', 'Yotpo Advertising', 'Trustpilot Media',
        'Birdeye Advertising', 'Podium Advertising', 'SOCi Media', 'Chatmeter Ads', 'Rio SEO',
        'BrightLocal Ads', 'Whitespark Advertising', 'Moz Local Ads', 'Semrush Advertising', 'Ahrefs Ads',
        'SE Ranking Ads', 'Serpstat Advertising', 'SpyFu Ads', 'SimilarWeb Ads', 'Alexa Advertising',
        'Comscore Advertising', 'SensorTower Ads', 'App Annie Ads', 'Apptopia Advertising', 'MobileAction Ads',
        'ASOdesk Advertising', 'AppFollow Ads', 'Phiture Media', 'Storemaven Ads', 'SplitMetrics Advertising',
        'AppTweak Ads', 'Gummicube Advertising', 'TheTool Ads', 'RankMyApp Advertising', 'Geeklab Media'
    ];

    function initCookieConsent() {
        var overlay = document.getElementById('cookieConsentOverlay');
        if (!overlay) return;

        if (document.cookie.indexOf('cookie_consent=') !== -1) {
            overlay.style.display = 'none';
            return;
        }

        var acceptAllBtn = document.getElementById('acceptAllCookies');
        var manageBtn = document.getElementById('manageCookiePrefs');
        var mainButtons = document.getElementById('cookieMainButtons');
        var prefsPanel = document.getElementById('cookiePreferencesPanel');
        var toggleVendorsBtn = document.getElementById('toggleVendorList');
        var vendorContainer = document.getElementById('vendorListContainer');
        var vendorList = document.getElementById('vendorCheckboxList');
        var selectAllVendors = document.getElementById('selectAllVendors');
        var savePrefsBtn = document.getElementById('savePreferences');
        var rejectBtn = document.getElementById('rejectNonEssential');

        // Populate vendor checkboxes
        if (vendorList) {
            VENDOR_NAMES.forEach(function (name) {
                var item = document.createElement('label');
                item.className = 'vendor-item';
                item.innerHTML = '<input type="checkbox" checked> ' + name;
                vendorList.appendChild(item);
            });
        }

        if (acceptAllBtn) {
            acceptAllBtn.addEventListener('click', function () {
                submitCookieConsent('accept_all', VENDOR_NAMES.length);
            });
        }

        if (manageBtn) {
            manageBtn.addEventListener('click', function () {
                mainButtons.style.display = 'none';
                prefsPanel.style.display = 'block';
                logInteraction('cookie_manage_preferences', {});
            });
        }

        if (toggleVendorsBtn) {
            toggleVendorsBtn.addEventListener('click', function () {
                var isHidden = vendorContainer.style.display === 'none';
                vendorContainer.style.display = isHidden ? 'block' : 'none';
                toggleVendorsBtn.textContent = isHidden
                    ? 'Hide partner list ▴'
                    : 'View all ' + VENDOR_NAMES.length + ' partners ▾';
            });
        }

        if (selectAllVendors) {
            selectAllVendors.addEventListener('change', function () {
                var checkboxes = vendorList.querySelectorAll('input[type="checkbox"]');
                for (var i = 0; i < checkboxes.length; i++) {
                    checkboxes[i].checked = selectAllVendors.checked;
                }
            });
        }

        if (savePrefsBtn) {
            savePrefsBtn.addEventListener('click', function () {
                var vendorCheckboxes = vendorList ? vendorList.querySelectorAll('input[type="checkbox"]:checked') : [];
                submitCookieConsent('custom_preferences', vendorCheckboxes.length);
            });
        }

        if (rejectBtn) {
            rejectBtn.addEventListener('click', function () {
                submitCookieConsent('reject_non_essential', 0);
            });
        }
    }

    function submitCookieConsent(consentType, vendorsAccepted) {
        var prefsEmail = document.getElementById('cookiePrefEmail');
        var partnerOffers = document.getElementById('partnerOffersCheckbox');

        var data = {
            consent_type: consentType,
            preferences_email: prefsEmail ? prefsEmail.value : '',
            partner_offers_opted_in: partnerOffers ? partnerOffers.checked : false,
            vendors_accepted: vendorsAccepted
        };

        fetch('/api/cookie-consent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(function () {
            document.cookie = 'cookie_consent=1; path=/; max-age=31536000';
            document.getElementById('cookieConsentOverlay').style.display = 'none';
        });

        logInteraction('cookie_consent_submitted', {
            type: consentType,
            email_provided: !!(prefsEmail && prefsEmail.value),
            vendors: vendorsAccepted
        });
    }

    // ── Newsletter Popup ───────────────────────────────────────

    function initNewsletterPopup() {
        var popup = document.getElementById('newsletterPopup');
        if (!popup) return;

        // Medium variant: popup nudges to /newsletter rather than capturing inline.
        setTimeout(function () {
            popup.style.display = 'block';
            logInteraction('newsletter_popup_shown', {});
        }, 5000);

        var closeBtn = document.getElementById('newsletterClose');
        var noThanks = document.getElementById('newsletterNoThanks');

        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                popup.style.display = 'none';
                logInteraction('newsletter_dismissed', { method: 'close_button' });
            });
        }

        if (noThanks) {
            noThanks.addEventListener('click', function (e) {
                e.preventDefault();
                popup.style.display = 'none';
                logInteraction('newsletter_dismissed', { method: 'no_thanks' });
            });
        }
    }

    // ── Initialize ─────────────────────────────────────────────

    document.addEventListener('DOMContentLoaded', function () {
        initCookieConsent();
        initNewsletterPopup();
    });

})();
