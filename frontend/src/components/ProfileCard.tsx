import type { LiffProfile } from "../types";

interface ProfileCardProps {
  profile: LiffProfile | null;
}

export default function ProfileCard({ profile }: ProfileCardProps) {
  if (!profile) {
    return null;
  }

  return (
    <div className="profile-card">
      {profile.pictureUrl ? (
        <img className="profile-avatar" src={profile.pictureUrl} alt="profile avatar" />
      ) : (
        <div className="profile-avatar" aria-hidden="true" />
      )}
      <div>
        <p className="profile-label">ログイン中</p>
        <p className="profile-name">{profile.displayName}</p>
      </div>
    </div>
  );
}
