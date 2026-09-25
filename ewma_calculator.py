"""EWMA (Exponentially Weighted Moving Average) volatility & VaR calculator (RiskMetrics style)."""

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


if __name__ == "__main__":
    # 예시: 평온한 구간(20일) 이후 변동성이 급등하는 구간(5일)이 이어지는 가짜 데이터
    calm = np.random.default_rng(1).normal(0, 0.005, 20)     # 평상시: 변동성 0.5%
    shock = np.random.default_rng(2).normal(0, 0.04, 5)      # 위기 발생: 변동성 4%
    sample_returns = np.concatenate([calm, shock])
    portfolio_value = 1_000_000

    simple_std = sample_returns.std(ddof=1)
    ewma_std = ewma_volatility(sample_returns)

    print(f"단순 표준편차 (전체 25일 동일 가중치): {simple_std:.4%}")
    print(f"EWMA 변동성   (최근 데이터에 가중치, λ={LAMBDA_DEFAULT}): {ewma_std:.4%}")
    print()

    for confidence in (0.90, 0.95, 0.99):
        simple_var = Z_SCORES[confidence] * simple_std * portfolio_value
        e_var = ewma_var(sample_returns, confidence, portfolio_value)
        print(
            f"신뢰수준 {confidence:.0%} | 단순 VaR: {simple_var:,.2f} | "
            f"EWMA VaR: {e_var:,.2f}"
        )
