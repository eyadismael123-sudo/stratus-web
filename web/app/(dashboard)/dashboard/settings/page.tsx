export const metadata = {
  title: "Settings — Stratus",
  description: "Manage your Stratus account settings.",
};

export default function SettingsPage() {
  return (
    <div className="min-h-screen" style={{ background: "#F5F5F7" }}>
      {/* Page header */}
      <div className="border-b border-black/[0.06] bg-[rgba(245,245,247,0.85)] backdrop-blur-[12px] sticky top-[60px] z-40 px-4 md:px-10 h-[60px] flex items-center">
        <span className="text-[17px] font-bold text-[#3A3A3C]">Settings</span>
      </div>

      <div className="px-4 md:px-10 py-8 max-w-2xl mx-auto flex flex-col gap-6">

        {/* Profile section */}
        <section
          className="bg-white rounded-[12px] border border-black/[0.06] overflow-hidden"
          style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
        >
          <div className="px-6 py-4 border-b border-black/[0.06]">
            <span className="text-[15px] font-bold text-[#3A3A3C]">Profile</span>
          </div>
          <form className="px-6 py-5 flex flex-col gap-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label className="flex flex-col gap-1.5">
                <span className="text-[12px] font-semibold text-[#6A6A6E] uppercase tracking-[0.4px]">
                  Full Name
                </span>
                <input
                  type="text"
                  defaultValue="Eyad Ismael"
                  className="h-[42px] px-3.5 rounded-[8px] border border-[#D2D2D7] bg-white text-[14px] text-[#3A3A3C] outline-none focus:border-[#3A3A3C] transition-colors"
                />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-[12px] font-semibold text-[#6A6A6E] uppercase tracking-[0.4px]">
                  Company
                </span>
                <input
                  type="text"
                  defaultValue="Stratus"
                  className="h-[42px] px-3.5 rounded-[8px] border border-[#D2D2D7] bg-white text-[14px] text-[#3A3A3C] outline-none focus:border-[#3A3A3C] transition-colors"
                />
              </label>
            </div>
            <label className="flex flex-col gap-1.5">
              <span className="text-[12px] font-semibold text-[#6A6A6E] uppercase tracking-[0.4px]">
                Email
              </span>
              <input
                type="email"
                defaultValue="eyad@stratus.ai"
                className="h-[42px] px-3.5 rounded-[8px] border border-[#D2D2D7] bg-[#F5F5F7] text-[14px] text-[#8E8E93] outline-none cursor-not-allowed"
                disabled
              />
              <span className="text-[11px] text-[#8E8E93]">
                Email cannot be changed. Contact support if needed.
              </span>
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-[12px] font-semibold text-[#6A6A6E] uppercase tracking-[0.4px]">
                Timezone
              </span>
              <select className="h-[42px] px-3.5 rounded-[8px] border border-[#D2D2D7] bg-white text-[14px] text-[#3A3A3C] outline-none focus:border-[#3A3A3C] transition-colors cursor-pointer">
                <option value="Asia/Dubai">Asia/Dubai (GMT+4)</option>
                <option value="Asia/Riyadh">Asia/Riyadh (GMT+3)</option>
                <option value="Europe/London">Europe/London (GMT+0)</option>
                <option value="America/New_York">America/New_York (GMT-5)</option>
              </select>
            </label>
            <div className="flex justify-end pt-1">
              <button
                type="submit"
                className="h-[38px] px-6 rounded-[8px] text-[13px] font-bold text-white bg-[#3A3A3C] hover:bg-[#2a2a2c] transition-all cursor-pointer border-none"
              >
                Save Changes
              </button>
            </div>
          </form>
        </section>

        {/* Security section */}
        <section
          className="bg-white rounded-[12px] border border-black/[0.06] overflow-hidden"
          style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
        >
          <div className="px-6 py-4 border-b border-black/[0.06]">
            <span className="text-[15px] font-bold text-[#3A3A3C]">Security</span>
          </div>
          <div className="px-6 py-5 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[14px] font-semibold text-[#3A3A3C]">Password</div>
                <div className="text-[12px] text-[#6A6A6E] mt-0.5">Last changed 30 days ago</div>
              </div>
              <button className="h-[34px] px-4 rounded-[8px] text-[12px] font-semibold text-[#3A3A3C] border border-[#D2D2D7] bg-transparent hover:border-[#3A3A3C] transition-all cursor-pointer">
                Change Password
              </button>
            </div>
          </div>
        </section>

        {/* Notifications section */}
        <section
          className="bg-white rounded-[12px] border border-black/[0.06] overflow-hidden"
          style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
        >
          <div className="px-6 py-4 border-b border-black/[0.06]">
            <span className="text-[15px] font-bold text-[#3A3A3C]">Notifications</span>
          </div>
          <div className="px-6 py-5 flex flex-col gap-4">
            {[
              { label: "Agent run completed", desc: "Get notified when an agent finishes a task" },
              { label: "Agent errors", desc: "Immediate alerts when an agent fails" },
              { label: "Billing updates", desc: "Invoices, renewals, and payment issues" },
            ].map(({ label, desc }) => (
              <div key={label} className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-[13px] font-semibold text-[#3A3A3C]">{label}</div>
                  <div className="text-[12px] text-[#6A6A6E] mt-0.5">{desc}</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                  <input type="checkbox" defaultChecked className="sr-only peer" />
                  <div className="w-10 h-6 bg-[#D2D2D7] rounded-full peer peer-checked:bg-[#3A3A3C] transition-colors" />
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
                </label>
              </div>
            ))}
          </div>
        </section>

        {/* Danger zone */}
        <section
          className="bg-white rounded-[12px] border border-[#FF3B30]/20 overflow-hidden"
          style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}
        >
          <div className="px-6 py-4 border-b border-[#FF3B30]/10">
            <span className="text-[15px] font-bold text-[#3A3A3C]">Danger Zone</span>
          </div>
          <div className="px-6 py-5 flex items-center justify-between gap-4">
            <div>
              <div className="text-[14px] font-semibold text-[#3A3A3C]">Delete Account</div>
              <div className="text-[12px] text-[#6A6A6E] mt-0.5">
                Permanently removes your account and all data. This cannot be undone.
              </div>
            </div>
            <button className="h-[34px] px-4 rounded-[8px] text-[12px] font-semibold text-[#FF3B30] border border-[#FF3B30]/30 bg-transparent hover:bg-[#FF3B30]/[0.04] transition-all cursor-pointer flex-shrink-0">
              Delete Account
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
