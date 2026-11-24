/**
 * Site-wide notice shown while the backend is offline. The Azure Container
 * App behind API_BASE was deleted after the credits ran out, so every API
 * call fails until it is redeployed. Remove this banner once it's back.
 */
export function OutageBanner() {
  return (
    <div className="outage-banner" role="status">
      <p>
        <b>Sorry, I ran out of Azure credits LOL.</b>
        Recipes and the assistant are offline for now. They'll be back once I
        find the server some new money.
      </p>
    </div>
  );
}
