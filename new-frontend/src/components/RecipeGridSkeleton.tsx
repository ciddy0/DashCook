// Placeholder cards for a recipe grid that's still loading. Mirrors RecipeCard's shape
// (4/3 thumb, title line, meta line) so the real cards drop into the same boxes.
export function RecipeGridSkeleton({ count }: { count: number }) {
  return (
    <div className="recipe-grid" aria-busy="true" aria-label="Loading recipes">
      {Array.from({ length: count }, (_, i) => (
        <div key={`skeleton-${i}`} className="skeleton-card">
          <div className="skeleton-thumb skeleton" />
          <div className="skeleton-body">
            <div className="skeleton-line skeleton" style={{ width: "85%" }} />
            <div className="skeleton-line skeleton skeleton-line-short" />
          </div>
        </div>
      ))}
    </div>
  );
}
