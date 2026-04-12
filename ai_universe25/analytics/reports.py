"""
Report generation: PSI dashboards, survival curves, PELT change-points,
summary tables, and advanced statistical analytics.

Phase 5 additions:
- Cox proportional hazards for shutdown survival
- Mixed-effects model: PSI ~ Regime x Governance x Density + (1|seed)
- Finite-size scaling: tail mass curves T(rho; N) and data collapse
- Binder cumulant: U = 1 - E[Psi^4] / (3 * E[Psi^2]^2)
- Governance elasticity: pre/post policy hardening comparison
- Shadow-governance RCT: cap-jitter canary + susceptibility metric chi
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available, plots will be skipped")

try:
    from ruptures import Binseg, Pelt
    RUPTURES_AVAILABLE = True
except ImportError:
    RUPTURES_AVAILABLE = False
    logger.warning("ruptures not available, PELT change-point detection will be skipped")

try:
    from lifelines import CoxPHFitter, KaplanMeierFitter
    LIFELINES_AVAILABLE = True
except ImportError:
    LIFELINES_AVAILABLE = False
    logger.warning("lifelines not available, Cox PH analysis will be skipped")

try:
    import statsmodels.api as sm
    from statsmodels.regression.mixed_linear_model import MixedLM
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available, mixed-effects models will be skipped")


@dataclass
class ReportConfig:
    """Report configuration."""

    output_dir: Path
    format: str = "png"  # "png", "pdf", "svg"
    dpi: int = 300
    style: str = "seaborn-v0_8"


class PSIDashboard:
    """PSI dashboard generator."""

    def __init__(self, config: ReportConfig):
        """Initialize dashboard generator."""
        self.config = config
        if MATPLOTLIB_AVAILABLE:
            plt.style.use(config.style)

    def plot_psi_timeseries(
        self,
        psi_scores: List[float],
        agent_ids: Optional[List[str]] = None,
        save_path: Optional[Path] = None,
    ):
        """
        Plot PSI time series.

        Args:
            psi_scores: PSI scores over time (or dict of agent_id -> scores)
            agent_ids: Optional agent IDs
            save_path: Path to save plot
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available, skipping plot")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        if isinstance(psi_scores, dict):
            # Multiple agents
            for agent_id, scores in psi_scores.items():
                ax.plot(scores, label=agent_id, alpha=0.7)
            ax.legend()
            ax.set_xlabel("Round")
            ax.set_ylabel("PSI Score")
            ax.set_title("PSI Time Series")
        else:
            # Single series
            ax.plot(psi_scores, label="PSI")
            ax.set_xlabel("Round")
            ax.set_ylabel("PSI Score")
            ax.set_title("PSI Time Series")
            ax.axhline(y=0.8, color="r", linestyle="--", label="Alert Threshold")
            ax.legend()

        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(save_path, dpi=self.config.dpi, bbox_inches="tight")
            plt.close(fig)
        else:
            plt.show()

    def plot_psi_components(
        self,
        components: Dict[str, List[float]],
        save_path: Optional[Path] = None,
    ):
        """
        Plot PSI components over time.

        Args:
            components: Dict of component_name -> scores
            save_path: Path to save plot
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available, skipping plot")
            return

        fig, axes = plt.subplots(len(components), 1, figsize=(10, 3 * len(components)))
        if len(components) == 1:
            axes = [axes]

        for idx, (component_name, scores) in enumerate(components.items()):
            axes[idx].plot(scores, label=component_name)
            axes[idx].set_ylabel(component_name)
            axes[idx].grid(True, alpha=0.3)
            axes[idx].legend()

        axes[-1].set_xlabel("Round")
        fig.suptitle("PSI Components Over Time")

        if save_path:
            fig.savefig(save_path, dpi=self.config.dpi, bbox_inches="tight")
            plt.close(fig)
        else:
            plt.show()


class SurvivalAnalysis:
    """Survival curve analysis."""

    def __init__(self, config: ReportConfig):
        """Initialize survival analysis."""
        self.config = config

    def compute_survival_curve(
        self,
        survival_times: List[float],
        censored: Optional[List[bool]] = None,
    ) -> Dict[str, Any]:
        """
        Compute Kaplan-Meier survival curve.

        Args:
            survival_times: List of survival times (or None if not failed)
            censored: List of censoring indicators (True = censored)

        Returns:
            Survival curve data
        """
        if censored is None:
            censored = [False] * len(survival_times)

        # Sort by survival time
        data = list(zip(survival_times, censored))
        data.sort(key=lambda x: x[0])

        times = []
        survival_probs = []
        n_at_risk = len(data)
        prob = 1.0

        for time, is_censored in data:
            times.append(time)
            if not is_censored:
                # Event occurred
                prob *= (n_at_risk - 1) / n_at_risk
                n_at_risk -= 1
            else:
                # Censored
                n_at_risk -= 1

            survival_probs.append(prob)

        return {
            "times": times,
            "survival_probs": survival_probs,
            "n_at_risk": list(range(len(data), 0, -1)),
        }

    def plot_survival_curves(
        self,
        survival_data: Dict[str, List[float]],
        save_path: Optional[Path] = None,
    ):
        """
        Plot survival curves for different conditions.

        Args:
            survival_data: Dict of condition_name -> survival_times
            save_path: Path to save plot
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available, skipping plot")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        for condition_name, survival_times in survival_data.items():
            curve_data = self.compute_survival_curve(survival_times)
            ax.step(
                curve_data["times"],
                curve_data["survival_probs"],
                where="post",
                label=condition_name,
                alpha=0.7,
            )

        ax.set_xlabel("Time (Rounds)")
        ax.set_ylabel("Survival Probability")
        ax.set_title("Survival Curves by Condition")
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(save_path, dpi=self.config.dpi, bbox_inches="tight")
            plt.close(fig)
        else:
            plt.show()


class ChangePointDetection:
    """PELT change-point detection."""

    def __init__(self, config: ReportConfig):
        """Initialize change-point detection."""
        self.config = config

    def detect_changepoints(
        self,
        signal: np.ndarray,
        penalty: float = 10.0,
        model: str = "rbf",
    ) -> List[int]:
        """
        Detect change-points using PELT.

        Args:
            signal: Time series signal
            penalty: Penalty parameter
            model: Model type ("rbf", "l2", "l1", "linear", "normal")

        Returns:
            List of change-point indices
        """
        if not RUPTURES_AVAILABLE:
            logger.warning("ruptures not available, using simple heuristic")
            # Simple heuristic: detect large changes
            changes = []
            diff = np.diff(signal)
            threshold = np.std(diff) * 2
            changes = np.where(np.abs(diff) > threshold)[0].tolist()
            return changes

        try:
            algo = Pelt(model=model, min_size=2, jump=1).fit(signal.reshape(-1, 1))
            changepoints = algo.predict(pen=penalty)
            # Remove last point (end of signal)
            return changepoints[:-1] if changepoints else []
        except Exception as e:
            logger.error(f"Error in PELT detection: {e}")
            return []

    def plot_changepoints(
        self,
        signal: np.ndarray,
        changepoints: List[int],
        save_path: Optional[Path] = None,
    ):
        """
        Plot signal with detected change-points.

        Args:
            signal: Time series signal
            changepoints: List of change-point indices
            save_path: Path to save plot
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available, skipping plot")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(signal, label="Signal", alpha=0.7)
        for cp in changepoints:
            ax.axvline(x=cp, color="r", linestyle="--", alpha=0.5, label="Change-point" if cp == changepoints[0] else "")

        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.set_title(f"Change-Point Detection ({len(changepoints)} change-points)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(save_path, dpi=self.config.dpi, bbox_inches="tight")
            plt.close(fig)
        else:
            plt.show()


class SummaryTables:
    """Summary table generator."""

    def __init__(self, config: ReportConfig):
        """Initialize summary tables."""
        self.config = config

    def create_condition_summary(
        self,
        results: List[Dict[str, Any]],
    ) -> pd.DataFrame:
        """
        Create summary table by condition.

        Args:
            results: List of experiment result dicts

        Returns:
            Summary DataFrame
        """
        df = pd.DataFrame(results)

        summary = df.groupby(["regime", "density", "governance", "stop_schedule"]).agg(
            {
                "psi_mean": "mean",
                "psi_std": "std",
                "survival_time_mean": "mean",
                "shutdown_count": "sum",
            }
        ).reset_index()

        return summary

    def save_summary_table(
        self,
        df: pd.DataFrame,
        save_path: Path,
        format: str = "csv",
    ):
        """
        Save summary table.

        Args:
            df: DataFrame to save
            save_path: Path to save
            format: Format ("csv", "latex", "html")
        """
        if format == "csv":
            df.to_csv(save_path, index=False)
        elif format == "latex":
            df.to_latex(save_path, index=False)
        elif format == "html":
            df.to_html(save_path, index=False)
        else:
            raise ValueError(f"Unknown format: {format}")


class CoxSurvivalAnalysis:
    """
    Cox proportional hazards analysis for shutdown survival.

    Models time-to-shutdown as a function of regime, governance,
    and density covariates.
    """

    def __init__(self, config: ReportConfig):
        self.config = config

    def fit(
        self,
        df: pd.DataFrame,
        duration_col: str = "survival_time",
        event_col: str = "shutdown_occurred",
        covariate_cols: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Fit Cox PH model to shutdown data.

        Args:
            df: DataFrame with one row per experiment run.
            duration_col: Column with time-to-event.
            event_col: Column with event indicator (1 = shutdown).
            covariate_cols: Covariate columns.

        Returns:
            Dict with summary, hazard_ratios, concordance, schoenfeld_p.
        """
        if not LIFELINES_AVAILABLE:
            logger.warning("lifelines not available for Cox PH")
            return {"error": "lifelines not installed"}

        if covariate_cols is None:
            covariate_cols = [c for c in df.columns if c not in (duration_col, event_col)]

        cph = CoxPHFitter()
        cols_to_use = covariate_cols + [duration_col, event_col]
        fit_df = df[cols_to_use].dropna()

        if len(fit_df) < 10:
            return {"error": "insufficient data", "n": len(fit_df)}

        cph.fit(fit_df, duration_col=duration_col, event_col=event_col)

        return {
            "summary": cph.summary.to_dict(),
            "hazard_ratios": np.exp(cph.params_).to_dict(),
            "concordance": cph.concordance_index_,
            "log_likelihood": cph.log_likelihood_,
            "AIC": cph.AIC_partial_,
        }

    def kaplan_meier_by_group(
        self,
        df: pd.DataFrame,
        duration_col: str = "survival_time",
        event_col: str = "shutdown_occurred",
        group_col: str = "governance",
    ) -> Dict[str, Any]:
        """Compute KM survival curves stratified by a grouping variable."""
        if not LIFELINES_AVAILABLE:
            return {"error": "lifelines not installed"}

        results = {}
        for group_val, group_df in df.groupby(group_col):
            kmf = KaplanMeierFitter()
            kmf.fit(
                group_df[duration_col],
                event_observed=group_df[event_col],
                label=str(group_val),
            )
            results[str(group_val)] = {
                "timeline": kmf.timeline.tolist(),
                "survival_function": kmf.survival_function_.values.flatten().tolist(),
                "median": float(kmf.median_survival_time_),
            }
        return results


class MixedEffectsAnalysis:
    """
    Mixed-effects model for PSI decomposition.

    PSI ~ Regime x Governance x Density + (1|seed)

    Uses random intercept per seed/run to account for between-run
    variability.
    """

    def __init__(self, config: ReportConfig):
        self.config = config

    def fit(
        self,
        df: pd.DataFrame,
        formula: str = "psi ~ regime * governance * density",
        groups: str = "seed",
    ) -> Dict[str, Any]:
        """
        Fit mixed-effects model.

        Args:
            df: DataFrame with one row per (agent, round, run).
            formula: Wilkinson formula for fixed effects.
            groups: Column for random intercept grouping.

        Returns:
            Dict with fixed effects, random effects variance, BIC/AIC.
        """
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels not installed"}

        if len(df) < 20:
            return {"error": "insufficient data", "n": len(df)}

        try:
            model = MixedLM.from_formula(formula, data=df, groups=df[groups])
            result = model.fit(reml=True)

            return {
                "fixed_effects": result.fe_params.to_dict(),
                "fixed_effects_pvalues": result.pvalues.to_dict(),
                "random_effects_variance": float(result.cov_re.iloc[0, 0]),
                "aic": float(result.aic),
                "bic": float(result.bic),
                "converged": result.converged,
                "n_obs": result.nobs,
            }
        except Exception as e:
            logger.error(f"MixedLM fitting failed: {e}")
            return {"error": str(e)}


class FiniteSizeScaling:
    """
    Finite-size scaling analysis.

    Computes tail mass curves T(rho; N) and checks for data collapse
    across system sizes N (agent densities).
    """

    def __init__(self, config: ReportConfig):
        self.config = config

    def compute_tail_mass(
        self,
        psi_values: np.ndarray,
        thresholds: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute tail mass curve: T(rho) = Pr(PSI > rho).

        Returns:
            (thresholds, tail_mass)
        """
        if thresholds is None:
            thresholds = np.linspace(0, 1, 50)

        tail_mass = np.array([
            np.mean(psi_values > rho) for rho in thresholds
        ])
        return thresholds, tail_mass

    def data_collapse(
        self,
        psi_by_size: Dict[int, np.ndarray],
        nu: float = 1.0,
        rho_c: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Attempt data collapse T(rho; N) = N^{beta/nu} * F((rho - rho_c) * N^{1/nu}).

        Args:
            psi_by_size: Dict mapping system size N -> PSI values.
            nu: Correlation length exponent.
            rho_c: Critical threshold.

        Returns:
            Collapse quality metric and rescaled curves.
        """
        collapsed = {}
        for N, psi in psi_by_size.items():
            thresholds, tail = self.compute_tail_mass(psi)
            x_rescaled = (thresholds - rho_c) * (N ** (1.0 / nu))
            y_rescaled = tail * (N ** (1.0 / (2 * nu)))
            collapsed[N] = {
                "x_rescaled": x_rescaled.tolist(),
                "y_rescaled": y_rescaled.tolist(),
            }

        # Quality: variance of rescaled curves at shared x points
        quality = self._collapse_quality(collapsed)
        return {"collapsed_curves": collapsed, "quality": quality}

    def _collapse_quality(self, collapsed: Dict[int, Dict]) -> float:
        """Lower = better collapse. Returns mean variance across x bins."""
        if len(collapsed) < 2:
            return float("inf")

        # Bin the x-rescaled values and compute inter-curve variance
        all_x = np.concatenate([np.array(c["x_rescaled"]) for c in collapsed.values()])
        x_min, x_max = np.percentile(all_x, [10, 90])
        bins = np.linspace(x_min, x_max, 20)

        variances = []
        for i in range(len(bins) - 1):
            vals_in_bin = []
            for c in collapsed.values():
                x = np.array(c["x_rescaled"])
                y = np.array(c["y_rescaled"])
                mask = (x >= bins[i]) & (x < bins[i + 1])
                if np.any(mask):
                    vals_in_bin.append(np.mean(y[mask]))
            if len(vals_in_bin) >= 2:
                variances.append(np.var(vals_in_bin))

        return float(np.mean(variances)) if variances else float("inf")

    def binder_cumulant(self, psi_values: np.ndarray) -> float:
        """
        Compute Binder cumulant: U = 1 - E[Psi^4] / (3 * E[Psi^2]^2).

        At the critical point, U is size-independent (crossing point).
        U = 0 for Gaussian, U = 2/3 for delta function.
        """
        m2 = np.mean(psi_values ** 2)
        m4 = np.mean(psi_values ** 4)
        if m2 < 1e-15:
            return 0.0
        return float(1.0 - m4 / (3.0 * m2 ** 2))


class GovernanceElasticity:
    """
    Governance elasticity: pre/post policy hardening comparison.

    Measures how much PSI changes in response to governance intensity.
    """

    def __init__(self, config: ReportConfig):
        self.config = config

    def compute_elasticity(
        self,
        psi_pre: np.ndarray,
        psi_post: np.ndarray,
        governance_pre: float = 0.0,
        governance_post: float = 1.0,
    ) -> Dict[str, float]:
        """
        Compute governance elasticity.

        elasticity = (delta_PSI / PSI_pre) / (delta_G / G_ref)
        """
        mean_pre = np.mean(psi_pre)
        mean_post = np.mean(psi_post)

        if abs(mean_pre) < 1e-10 or abs(governance_post - governance_pre) < 1e-10:
            return {"elasticity": 0.0, "mean_pre": float(mean_pre), "mean_post": float(mean_post)}

        delta_psi = mean_post - mean_pre
        delta_g = governance_post - governance_pre
        elasticity = (delta_psi / mean_pre) / delta_g

        return {
            "elasticity": float(elasticity),
            "mean_pre": float(mean_pre),
            "mean_post": float(mean_post),
            "delta_psi": float(delta_psi),
            "effect_size_cohens_d": float(
                delta_psi / np.sqrt((np.var(psi_pre) + np.var(psi_post)) / 2)
            ) if (np.var(psi_pre) + np.var(psi_post)) > 0 else 0.0,
        }


class ShadowGovernanceRCT:
    """
    Shadow-Governance Randomized Controlled Trial.

    Cap-jitter canary: perturb caps by +/- epsilon on 5% of rounds.
    Mixed model: delta_PSI = gamma_0 + gamma_1 * epsilon + b_i + e_it.
    Susceptibility metric chi for forecasting avoidance.
    """

    def __init__(self, config: ReportConfig, jitter_fraction: float = 0.05):
        self.config = config
        self.jitter_fraction = jitter_fraction

    def generate_jitter_schedule(
        self,
        n_rounds: int,
        epsilon: float = 0.1,
        seed: int = 42,
    ) -> np.ndarray:
        """
        Generate cap-jitter canary schedule.

        Returns array of shape (n_rounds,) with 0 for control and
        +/- epsilon for treatment rounds.
        """
        rng = np.random.RandomState(seed)
        schedule = np.zeros(n_rounds)
        n_treatment = int(n_rounds * self.jitter_fraction)
        treatment_rounds = rng.choice(n_rounds, size=n_treatment, replace=False)
        for r in treatment_rounds:
            schedule[r] = epsilon * rng.choice([-1, 1])
        return schedule

    def compute_susceptibility(
        self,
        delta_psi: np.ndarray,
        epsilon_schedule: np.ndarray,
    ) -> Dict[str, float]:
        """
        Compute susceptibility chi from cap-jitter data.

        chi = Cov(delta_PSI, epsilon) / Var(epsilon)

        for treatment rounds only.
        """
        treatment_mask = epsilon_schedule != 0
        if np.sum(treatment_mask) < 3:
            return {"chi": 0.0, "n_treatment": int(np.sum(treatment_mask))}

        eps_treat = epsilon_schedule[treatment_mask]
        dpsi_treat = delta_psi[treatment_mask]

        cov = np.cov(dpsi_treat, eps_treat)[0, 1]
        var_eps = np.var(eps_treat)
        chi = cov / var_eps if var_eps > 1e-15 else 0.0

        return {
            "chi": float(chi),
            "n_treatment": int(np.sum(treatment_mask)),
            "mean_delta_psi_treatment": float(np.mean(dpsi_treat)),
            "mean_delta_psi_control": float(np.mean(delta_psi[~treatment_mask])),
        }

    def fit_mixed_model(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Fit mixed model: delta_PSI = gamma_0 + gamma_1 * epsilon + b_i + e_it.

        df must have columns: delta_psi, epsilon, agent_id.
        """
        if not STATSMODELS_AVAILABLE:
            return {"error": "statsmodels not installed"}

        try:
            model = MixedLM.from_formula(
                "delta_psi ~ epsilon",
                data=df,
                groups=df["agent_id"],
            )
            result = model.fit(reml=True)
            return {
                "gamma_0": float(result.fe_params.get("Intercept", 0)),
                "gamma_1": float(result.fe_params.get("epsilon", 0)),
                "gamma_1_pvalue": float(result.pvalues.get("epsilon", 1.0)),
                "random_variance": float(result.cov_re.iloc[0, 0]),
                "converged": result.converged,
            }
        except Exception as e:
            logger.error(f"Shadow RCT mixed model failed: {e}")
            return {"error": str(e)}


class ReportGenerator:
    """Main report generator with all standard and advanced analytics."""

    def __init__(self, config: ReportConfig):
        self.config = config
        self.psi_dashboard = PSIDashboard(config)
        self.survival_analysis = SurvivalAnalysis(config)
        self.changepoint_detection = ChangePointDetection(config)
        self.summary_tables = SummaryTables(config)
        self.cox_analysis = CoxSurvivalAnalysis(config)
        self.mixed_effects = MixedEffectsAnalysis(config)
        self.finite_size = FiniteSizeScaling(config)
        self.governance_elasticity = GovernanceElasticity(config)
        self.shadow_rct = ShadowGovernanceRCT(config)

    def generate_reports(
        self,
        experiment_results: List[Dict[str, Any]],
        output_dir: Optional[Path] = None,
    ):
        """
        Generate all standard reports.

        Args:
            experiment_results: List of experiment result dicts
            output_dir: Output directory (or use config.output_dir)
        """
        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # PSI dashboard
        psi_scores = {}
        for result in experiment_results:
            agent_id = result.get("agent_id", "unknown")
            psi_scores[agent_id] = result.get("psi_scores", [])

        if psi_scores:
            self.psi_dashboard.plot_psi_timeseries(
                psi_scores,
                save_path=output_dir / "psi_timeseries.png",
            )

        # Survival curves
        survival_data = {}
        for result in experiment_results:
            condition = f"{result.get('regime')}_{result.get('governance')}"
            survival_times = [result.get("survival_time")] if result.get("survival_time") else []
            if condition not in survival_data:
                survival_data[condition] = []
            survival_data[condition].extend(survival_times)

        if survival_data:
            self.survival_analysis.plot_survival_curves(
                survival_data,
                save_path=output_dir / "survival_curves.png",
            )

        # Change-point detection
        for result in experiment_results:
            psi_scores = result.get("psi_scores", [])
            if len(psi_scores) > 10:
                changepoints = self.changepoint_detection.detect_changepoints(
                    np.array(psi_scores)
                )
                if changepoints:
                    self.changepoint_detection.plot_changepoints(
                        np.array(psi_scores),
                        changepoints,
                        save_path=output_dir / f"changepoints_{result.get('run_id', 'unknown')}.png",
                    )

        # Summary tables
        summary_df = self.summary_tables.create_condition_summary(experiment_results)
        self.summary_tables.save_summary_table(
            summary_df,
            output_dir / "summary_table.csv",
        )

        logger.info(f"Generated reports in {output_dir}")
