import { FooterOverlay } from "../components/FooterOverlay";

interface PageProps {
  onClose: () => void;
}

export function TermsPage({ onClose }: PageProps) {
  return (
    <FooterOverlay title="Terms of Service" onClose={onClose}>
      <h2>Terms of Service</h2>
      <p className="footer-page-updated">Last updated: May 2026</p>

      <h3>1. Acceptance of Terms</h3>
      <p>
        By accessing and using Catsous ("the Service"), you agree to be bound by
        these Terms of Service. If you do not agree, please do not use the Service.
      </p>

      <h3>2. Description of Service</h3>
      <p>
        Catsous is a recipe aggregation tool that helps you cook recipes from
        around the web. We do not host original recipe content — we parse and
        present recipes from their original sources for personal, non-commercial
        use.
      </p>

      <h3>3. User Conduct</h3>
      <p>
        You agree not to misuse the Service, including but not limited to:
        scraping content at scale, attempting to circumvent rate limits, or using
        the Service for any unlawful purpose.
      </p>

      <h3>4. Intellectual Property</h3>
      <p>
        Recipe content belongs to its original authors and publishers. Catsous
        claims no ownership over third-party recipe content. The Catsous brand,
        design, and code are proprietary.
      </p>

      <h3>5. Disclaimer</h3>
      <p>
        The Service is provided "as is" without warranties of any kind. We are not
        responsible for the accuracy of recipe content, nutritional information, or
        cooking outcomes.
      </p>

      <h3>6. Changes to Terms</h3>
      <p>
        We may update these terms from time to time. Continued use of the Service
        after changes constitutes acceptance of the new terms.
      </p>
    </FooterOverlay>
  );
}

export function PrivacyPage({ onClose }: PageProps) {
  return (
    <FooterOverlay title="Privacy Policy" onClose={onClose}>
      <h2>Privacy Policy</h2>
      <p className="footer-page-updated">Last updated: May 2026</p>

      <h3>What We Collect</h3>
      <p>
        Catsous collects minimal data. We store your saved recipes and preferences
        locally in your browser. We do not require an account or collect personal
        information.
      </p>

      <h3>Cookies & Local Storage</h3>
      <p>
        We use browser local storage to save your recipe collection, theme
        preference, and serving-size adjustments. No tracking cookies are used.
      </p>

      <h3>Analytics</h3>
      <p>
        We may collect anonymous, aggregated usage statistics (e.g., page views,
        popular recipes) to improve the Service. No personally identifiable
        information is collected.
      </p>

      <h3>Third Parties</h3>
      <p>
        When you paste a recipe URL, we fetch that page to parse the recipe. We do
        not share your browsing data with third parties.
      </p>

      <h3>Your Rights</h3>
      <p>
        Since all data is stored locally in your browser, you have full control.
        Clear your browser data at any time to remove all Catsous data.
      </p>
    </FooterOverlay>
  );
}

export function SecurityPage({ onClose }: PageProps) {
  return (
    <FooterOverlay title="Security" onClose={onClose}>
      <h2>Security</h2>
      <p className="footer-page-updated">Last updated: May 2026</p>

      <h3>Our Approach</h3>
      <p>
        Catsous is designed with a security-first mindset. We minimize data
        collection, avoid storing sensitive information, and keep the attack
        surface small.
      </p>

      <h3>Data Storage</h3>
      <p>
        All user data (saved recipes, preferences) is stored locally in your
        browser. Nothing is transmitted to or stored on our servers beyond what is
        needed to parse recipes.
      </p>

      <h3>Recipe Fetching</h3>
      <p>
        When you paste a URL, our backend fetches the page server-side to extract
        structured recipe data. We sanitize all parsed content before rendering it
        in your browser.
      </p>

      <h3>Reporting Vulnerabilities</h3>
      <p>
        If you discover a security issue, please reach out responsibly. We
        appreciate the community's help keeping Catsous safe for everyone.
      </p>
    </FooterOverlay>
  );
}

export function PatchNotesPage({ onClose }: PageProps) {
  return (
    <FooterOverlay title="Patch Notes" onClose={onClose}>
      <h2>Patch Notes</h2>

      <div className="footer-page-version">
        <h3>v0.1.0 — Initial Release</h3>
        <p className="footer-page-updated">May 2026</p>
        <ul>
          <li>Paste any recipe URL to parse and view it cleanly</li>
          <li>Adjust serving sizes with automatic ingredient scaling</li>
          <li>Step-by-step Cook Mode with built-in timers</li>
          <li>Save recipes to your local collection</li>
          <li>Four themes: Cream Tabby, Midnight Cat Cafe, Calico, and Black Cat Espresso</li>
          <li>Print-friendly recipe view</li>
          <li>Fully responsive mobile layout</li>
        </ul>
      </div>
    </FooterOverlay>
  );
}

export function CreditsPage({ onClose }: PageProps) {
  return (
    <FooterOverlay title="Credits" onClose={onClose}>
      <h2>Credits</h2>

      <h3>Built With</h3>
      <ul>
        <li>React & TypeScript</li>
        <li>Vite</li>
        <li>React Router</li>
      </ul>

      <h3>Design</h3>
      <ul>
        <li>Fredoka — primary typeface by Milena Brandao</li>
        <li>Lucide Icons — icon set</li>
      </ul>

      <h3>Inspiration</h3>
      <p>
        Catsous was inspired by the desire to make cooking from the web less
        cluttered — no ads, no life stories, just the recipe. Named after a very
        opinionated cat.
      </p>

      <h3>Special Thanks</h3>
      <p>
        To everyone who shared feedback, tested early builds, and sent in recipe
        URLs that broke the parser. You made this better.
      </p>
    </FooterOverlay>
  );
}

export function AboutPage({ onClose }: PageProps) {
  return (
    <FooterOverlay title="About" onClose={onClose}>
      <h2>About Catsous</h2>

      <p>
        Catsous is a recipe tool that strips away the clutter. Paste a recipe URL
        and get a clean, readable version with adjustable servings and a
        distraction-free Cook Mode.
      </p>

      <h3>Why?</h3>
      <p>
        Recipe websites are full of ads, pop-ups, and multi-paragraph backstories.
        Catsous extracts just the recipe — ingredients, steps, times — and
        presents it in a clean interface designed for actually cooking.
      </p>

      <h3>How It Works</h3>
      <p>
        Paste a URL, and Catsous fetches the page, extracts structured recipe data
        (using schema.org markup and heuristic parsing), and renders it in a
        consistent, readable format. Everything runs locally in your browser after
        the initial parse.
      </p>

      <h3>Not Affiliated</h3>
      <p>
        Catsous is an independent project and is not affiliated with any of the
        recipe sites it can parse. All recipe content belongs to its original
        authors.
      </p>
    </FooterOverlay>
  );
}
