import { sevCls, sevTxt } from "../utils/format";
export const SeverityBadge = ({ value }: { value: unknown }) => <span className={`sv ${sevCls(value)}`}>● {sevTxt(value)}</span>;
