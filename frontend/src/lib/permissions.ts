export function canAccessAdmin(isSuperadmin: boolean): boolean {
  return Boolean(isSuperadmin);
}
