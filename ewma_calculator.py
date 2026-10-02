"""EWMA (Exponentially Weighted Moving Average) volatility & VaR calculator (RiskMetrics style)."""

import matplotlib.pyplot as plt
import numpy as np

# 표준정규분포의 단측 z값 (신뢰수준별)
Z_SCORES = {
    0.90: 1.2816,
    0.95: 1.6449,
    0.99: 2.3263,
}

LAMBDA_DEFAULT = 0.94  # RiskMetrics 표준값 (일별 데이터 기준)


def ewma_volatility(returns, lam=LAMBDA_DEFAULT):
    """어제까지의 변동성 + 어제 수익률 제곱을 재귀적으로 섞어 오늘의 변동성을 추정."""
    returns = np.asarray(returns)
    variance = returns[0] ** 2  # 첫날은 그 날의 제곱값으로 초기화
    for r in returns[1:]:
        variance = lam * variance + (1 - lam) * r ** 2
    return np.sqrt(variance)


def ewma_var(returns, confidence=0.95, portfolio_value=1.0, lam=LAMBDA_DEFAULT):
    """EWMA로 추정한 변동성 기반 VaR (RiskMetrics 관행대로 평균은 0으로 가정)."""
    if confidence not in Z_SCORES:
        raise ValueError(f"confidence must be one of {list(Z_SCORES)}")
    sigma = ewma_volatility(returns, lam)
    z = Z_SCORES[confidence]
    return z * sigma * portfolio_value


def ewma_volatility_path(returns, lam=LAMBDA_DEFAULT):
    """그래프용: 전체 기간에 걸친 EWMA 변동성 추정치의 경로를 반환."""
    returns = np.asarray(returns)
    n = len(returns)
    variance = np.empty(n)
    variance[0] = returns[0] ** 2
    for t in range(1, n):
        variance[t] = lam * variance[t - 1] + (1 - lam) * returns[t - 1] ** 2
    return np.sqrt(variance)


def plot_ewma_vs_simple(returns, lam=LAMBDA_DEFAULT, out_path="ewma_volatility.png"):
    """EWMA 변동성 경로(선) vs 전체기간 단순 표준편차(수평선)를 비교."""
    ewma_path = ewma_volatility_path(returns, lam)
    simple_std = returns.std(ddof=1)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(ewma_path, color="#C44E52", linewidth=1.5, label=f"EWMA volatility (lambda={lam})")
    ax.axhline(simple_std, color="#4C72B0", linestyle="--", linewidth=2,
               label=f"Simple std dev (whole period) = {simple_std:.2%}")
    ax.set_title("EWMA Volatility Reacts to Regime Changes Faster Than a Simple Average")
    ax.set_xlabel("Day")
    ax.set_ylabel("Daily Volatility")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"[안내] 차트를 '{out_path}'에 저장했습니다.")


if __name__ == "__main__":
    # 예시: 평온(60일) -> 변동성 급등(15일) -> 다시 평온(60일)으로 이어지는 가짜 데이터
    calm1 = np.random.default_rng(1).normal(0, 0.005, 60)    # 평상시: 변동성 0.5%
    shock = np.random.default_rng(2).normal(0, 0.04, 15)     # 위기 발생: 변동성 4%
    calm2 = np.random.default_rng(3).normal(0, 0.005, 60)    # 위기 종료 후 다시 평온
    sample_returns = np.concatenate([calm1, shock, calm2])
    portfolio_value = 1_000_000

    simple_std = sample_returns.std(ddof=1)
    ewma_std = ewma_volatility(sample_returns)

    print(f"단순 표준편차 (전체 {len(sample_returns)}일 동일 가중치): {simple_std:.4%}")
    print(f"EWMA 변동성   (최근 데이터에 가중치, λ={LAMBDA_DEFAULT}): {ewma_std:.4%}")
    print()

    for confidence in (0.90, 0.95, 0.99):
        simple_var = Z_SCORES[confidence] * simple_std * portfolio_value
        e_var = ewma_var(sample_returns, confidence, portfolio_value)
        print(
            f"신뢰수준 {confidence:.0%} | 단순 VaR: {simple_var:,.2f} | "
            f"EWMA VaR: {e_var:,.2f}"
        )

    plot_ewma_vs_simple(sample_returns)
