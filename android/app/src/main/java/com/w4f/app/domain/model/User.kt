package com.w4f.app.domain.model

enum class UserRole {
  ADMIN,
  MANAGER,
  EXPERT,
  MOQADDEM;

  companion object {
    fun fromApiValue(value: String): UserRole = valueOf(value.uppercase())
  }
}

enum class AppLanguage {
  AR,
  FR;

  companion object {
    fun fromApiValue(value: String): AppLanguage = valueOf(value.uppercase())
  }
}

data class Territory(val id: String, val nameAr: String, val nameFr: String, val level: String)

data class User(
  val id: String,
  val fullName: String,
  val email: String,
  val role: UserRole,
  val preferredLanguage: AppLanguage,
  val territories: List<Territory>,
)
