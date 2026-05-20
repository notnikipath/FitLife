import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const rawApiBase = import.meta.env.VITE_GATEWAY_URL || "/api";
const API_BASE = rawApiBase.replace(/\/$/, "");

function Stat({ label, value }) {
  return (
    <article className="stat-card">
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    fetch(`${API_BASE}/dashboard/USR-DEMO`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Dashboard request failed: ${response.status}`);
        }
        return response.json();
      })
      .then((payload) => {
        if (!ignore) {
          setData(payload);
        }
      })
      .catch((err) => {
        if (!ignore) {
          setError(err.message);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  const summary = useMemo(() => {
    if (!data) {
      return null;
    }
    const stats = data.progress?.stats || {};
    const nutrition = data.nutrition || {};
    const activities = data.activities || {};
    return {
      workouts: stats.workouts_total ?? 0,
      duration: stats.total_duration_minutes ?? 0,
      calories: stats.total_calories ?? 0,
      meals: nutrition.meals ?? 0,
      activityCount: activities.count ?? 0,
      weeklyLoad: stats.weekly_load ?? 0,
    };
  }, [data]);

  return (
    <main className="layout">
      <section className="hero">
        <div>
          <p className="eyebrow">FitLife</p>
          <h1>Personal Fitness Orchestration</h1>
          <p>
            Training plans, wearable logs, nutrition, achievements, and analytics in a single live dashboard.
          </p>
        </div>
        <span className="chip">Target: 1M users</span>
      </section>

      {error && <p className="error">{error}</p>}

      {!summary && !error && <p className="loading">Loading live metrics...</p>}

      {summary && (
        <>
          <section className="stats-grid">
            <Stat label="Workouts Total" value={summary.workouts} />
            <Stat label="Duration (min)" value={summary.duration} />
            <Stat label="Calories Burned" value={summary.calories} />
            <Stat label="Meals Logged" value={summary.meals} />
            <Stat label="Activities" value={summary.activityCount} />
            <Stat label="Weekly Load" value={summary.weeklyLoad} />
          </section>

          <section className="panels">
            <article>
              <h2>Next Recommendation</h2>
              <p className="highlight">{data.recommendations?.next_activity || "n/a"}</p>
              <p>{data.recommendations?.comment || "No recommendation yet."}</p>
            </article>

            <article>
              <h2>Nutrition Snapshot</h2>
              <p>Calories: {data.nutrition?.calories ?? 0}</p>
              <p>Protein: {data.nutrition?.protein ?? 0} g</p>
              <p>Fat: {data.nutrition?.fat ?? 0} g</p>
              <p>Carbs: {data.nutrition?.carbs ?? 0} g</p>
            </article>

            <article>
              <h2>Social Pulse</h2>
              <p>Feed items: {data.social_feed?.count ?? 0}</p>
              <p>Notifications: {data.notifications?.count ?? 0}</p>
              <p>Profile: {data.profile?.full_name || "USR-DEMO"}</p>
            </article>
          </section>
        </>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
