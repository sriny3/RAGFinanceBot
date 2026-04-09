export const DEMO_USERS = [
  {
    username: 'emp_john',
    name: 'John Employee',
    role: 'employee',
    department: 'General',
    color: 'bg-blue-100 border-blue-300',
    icon: '👤',
  },
  {
    username: 'fin_alice',
    name: 'Alice Finance',
    role: 'finance',
    department: 'Finance',
    color: 'bg-green-100 border-green-300',
    icon: '💰',
  },
  {
    username: 'eng_bob',
    name: 'Bob Engineer',
    role: 'engineering',
    department: 'Engineering',
    color: 'bg-purple-100 border-purple-300',
    icon: '⚙️',
  },
  {
    username: 'mkt_carol',
    name: 'Carol Marketing',
    role: 'marketing',
    department: 'Marketing',
    color: 'bg-pink-100 border-pink-300',
    icon: '📊',
  },
  {
    username: 'ceo_dave',
    name: 'Dave C-Level',
    role: 'c_level',
    department: 'Executive',
    color: 'bg-red-100 border-red-300',
    icon: '👑',
  },
];

export const ROLE_COLORS: Record<string, string> = {
  employee: 'bg-blue-50 text-blue-800 border-blue-200',
  finance: 'bg-green-50 text-green-800 border-green-200',
  engineering: 'bg-purple-50 text-purple-800 border-purple-200',
  marketing: 'bg-pink-50 text-pink-800 border-pink-200',
  c_level: 'bg-red-50 text-red-800 border-red-200',
};

export const COLLECTION_ICONS: Record<string, string> = {
  general: '📋',
  finance: '💰',
  engineering: '⚙️',
  marketing: '📊',
  hr: '👥',
};

export const GUARDRAIL_COLORS: Record<string, string> = {
  warning: 'bg-yellow-50 border-yellow-300 text-yellow-800',
  error: 'bg-red-50 border-red-300 text-red-800',
};
