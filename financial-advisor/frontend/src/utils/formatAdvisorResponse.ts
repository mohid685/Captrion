export const formatAdvisorResponse = (response: string) => response
  .replace(/\*\*/g, '')
  .replace(/\|\s*[-:]+(?:\s*\|\s*[-:]+)+\s*\|?/g, '')
  .replace(/\s*\|\s*/g, ' · ')
  .replace(/\s*·\s*Metric\s*·\s*Value\s*/i, '')
  .replace(/\s+-\s+(?=[A-Z])/g, '\n\n')
  .replace(/[ \t]+\n/g, '\n')
  .replace(/\n{3,}/g, '\n\n')
  .trim();
