export default class DateUtils {
  static formatDate(
    date?: string | Date | null,
    fallback: string = "Unknown"
  ): string {
    if (!date) return fallback;
    if (date instanceof Date) return date.toLocaleDateString();
    // Try to parse the date string
    const parsedDate = new Date(date);
    if (!isNaN(parsedDate.getTime())) {
      return parsedDate.toLocaleDateString();
    }
    return fallback;
  }
}
