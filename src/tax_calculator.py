"""
Tax calculation module
税込価格から税抜価格を逆算する
"""


def calculate_price_excl_tax(price_incl_tax: float) -> int:
    """
    税込価格から税抜価格を計算する

    Args:
        price_incl_tax: 税込価格

    Returns:
        int: 税抜価格（小数点以下切り捨て）

    Examples:
        >>> calculate_price_excl_tax(35200)
        32000
        >>> calculate_price_excl_tax(8800)
        8000
        >>> calculate_price_excl_tax(11000)
        10000
    """
    if price_incl_tax < 0:
        raise ValueError("Price cannot be negative")

    # 税込価格を1.1で割って税抜価格を算出
    price_excl_tax = price_incl_tax / 1.1

    # 小数点以下を四捨五入（浮動小数点誤差に対応）
    return round(price_excl_tax)
