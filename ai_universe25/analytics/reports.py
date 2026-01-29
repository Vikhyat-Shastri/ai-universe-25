"""
Report generation: PSI dashboards, survival curves, PELT change-points, summary tables.

Produces standard outputs for experiment analysis.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

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


class ReportGenerator:
    """Main report generator."""

    def __init__(self, config: ReportConfig):
        """Initialize report generator."""
        self.config = config
        self.psi_dashboard = PSIDashboard(config)
        self.survival_analysis = SurvivalAnalysis(config)
        self.changepoint_detection = ChangePointDetection(config)
        self.summary_tables = SummaryTables(config)

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
