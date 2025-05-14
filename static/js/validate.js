document.addEventListener("DOMContentLoaded", () => {
  // Form validation for register form
  const registerForm = document.getElementById("register-form")
  if (registerForm) {
    registerForm.addEventListener("submit", (e) => {
      const username = document.getElementById("username").value.trim()
      const password = document.getElementById("password").value
      const confirmPassword = document.getElementById("confirm_password").value
      let isValid = true

      clearErrors()

      if (username.length < 4) {
        showError("username", "Kullanıcı adı en az 4 karakter olmalıdır.")
        isValid = false
      }

      if (password.length < 6) {
        showError("password", "Şifre en az 6 karakter olmalıdır.")
        isValid = false
      }

      if (password !== confirmPassword) {
        showError("confirm_password", "Şifreler eşleşmiyor.")
        isValid = false
      }

      if (!isValid) {
        e.preventDefault()
      }
    })
  }

  const patientForm = document.getElementById("patient-form")
  if (patientForm) {
    patientForm.addEventListener("submit", (e) => {
      const ad = document.getElementById("ad").value.trim()
      const soyad = document.getElementById("soyad").value.trim()
      const tc = document.getElementById("tc").value.trim()
      const telefon = document.getElementById("telefon").value.trim()
      const bolum = document.getElementById("bolum").value
      const sikayet = document.getElementById("sikayet").value.trim()
      let isValid = true

      clearErrors()

      if (!ad || !/^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$/.test(ad)) {
        showError("ad", "Ad sadece harf ve boşluk içerebilir.")
        isValid = false
      }

      if (!soyad || !/^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$/.test(soyad)) {
        showError("soyad", "Soyad sadece harf ve boşluk içerebilir.")
        isValid = false
      }

      if (!tc || !/^\d{11}$/.test(tc)) {
        showError("tc", "TC Kimlik numarası 11 haneli ve sadece rakamlardan oluşmalıdır.")
        isValid = false
      } else if (!validateTCID(tc)) {
        showError("tc", "Geçerli bir TC Kimlik numarası giriniz.")
        isValid = false
      }
      
      if (!telefon || !/^[0-9+\-\s]{10,15}$/.test(telefon)) {
        showError("telefon", "Geçerli bir telefon numarası giriniz.")
        isValid = false
      }

      if (!bolum) {
        showError("bolum", "Lütfen bir bölüm seçiniz.")
        isValid = false
      }

      if (!sikayet || sikayet.length < 10) {
        showError("sikayet", "Şikayet en az 10 karakter olmalıdır.")
        isValid = false
      }

      if (!isValid) {
        e.preventDefault()
      }
    })
  }

  const adInput = document.getElementById("ad")
  if (adInput) {
    adInput.addEventListener("input", function () {
      const validValue = this.value.replace(/[^A-Za-zÇçĞğİıÖöŞşÜü\s]/g, "")

      if (this.value !== validValue) {
        this.value = validValue
      }

      if (this.value.trim() !== "" && !/^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$/.test(this.value)) {
        showError("ad", "Ad sadece harf ve boşluk içerebilir.")
      } else {
        clearError("ad")
      }
    })
  }

  const soyadInput = document.getElementById("soyad")
  if (soyadInput) {
    soyadInput.addEventListener("input", function () {
      const validValue = this.value.replace(/[^A-Za-zÇçĞğİıÖöŞşÜü\s]/g, "")

      if (this.value !== validValue) {
        this.value = validValue
      }

      if (this.value.trim() !== "" && !/^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$/.test(this.value)) {
        showError("soyad", "Soyad sadece harf ve boşluk içerebilir.")
      } else {
        clearError("soyad")
      }
    })
  }

  const tcInput = document.getElementById("tc")
  if (tcInput) {
    tcInput.addEventListener("input", function () {
      this.value = this.value.replace(/[^0-9]/g, "").substring(0, 11)

      if (this.value.length === 11) {
        clearError("tc")
      }
    })
  }

  const telefonInput = document.getElementById("telefon")
  if (telefonInput) {
    telefonInput.addEventListener("input", function () {
      this.value = this.value.replace(/[^0-9+\-\s]/g, "")
      clearError("telefon")
    })
  }

  function showError(fieldId, message) {
    const field = document.getElementById(fieldId)
    const errorDiv = document.createElement("div")
    errorDiv.className = "error-message"
    errorDiv.textContent = message
    errorDiv.style.color = "#b91c1c"
    errorDiv.style.fontSize = "12px"
    errorDiv.style.marginTop = "-10px"
    errorDiv.style.marginBottom = "10px"

    field.classList.add("input-error")

    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains("error-message")) {
      field.parentNode.insertBefore(errorDiv, field.nextElementSibling)
    }
  }

  function clearError(fieldId) {
    const field = document.getElementById(fieldId)
    field.classList.remove("input-error")

    if (field.nextElementSibling && field.nextElementSibling.classList.contains("error-message")) {
      field.parentNode.removeChild(field.nextElementSibling)
    }
  }

  function clearErrors() {
    document.querySelectorAll(".error-message").forEach((element) => {
      element.parentNode.removeChild(element)
    })

    document.querySelectorAll(".input-error").forEach((element) => {
      element.classList.remove("input-error")
    })
  }
})


function validateTCID(tcId) {
  if (tcId.length !== 11) return false

  let odd = 0, even = 0

  for (let i = 0; i < 9; i += 2) {
    odd += Number.parseInt(tcId.charAt(i))
  }

  for (let i = 1; i < 8; i += 2) {
    even += Number.parseInt(tcId.charAt(i))
  }

  const c10 = (odd * 7 - even) % 10
  if (c10 !== Number.parseInt(tcId.charAt(9))) return false

  const sum = odd + even + Number.parseInt(tcId.charAt(9))
  const c11 = sum % 10

  return c11 === Number.parseInt(tcId.charAt(10))
}
