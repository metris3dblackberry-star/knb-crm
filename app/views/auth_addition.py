
# =============================================================================
# EGYSZERŰ EMAIL/JELSZÓ BEJELENTKEZÉS (Neon Auth nélkül)
# =============================================================================

@auth_bp.route('/simple-login', methods=['POST'])
def simple_login():
    """Helyi email/jelszó bejelentkezés Neon Auth nélkül"""
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Adja meg az e-mail címét és jelszavát.'}), 400

    user = User.find_by_email(email)
    if not user or not user.check_password(password):
        return jsonify({'error': 'Hibás e-mail cím vagy jelszó.'}), 401

    if not user.is_active:
        return jsonify({'error': 'Ez a fiók le van tiltva.'}), 403

    auth_service = AuthService()
    auth_service.establish_session(user)
    session['auth_method'] = 'local'

    redirect_url = auth_service.resolve_post_auth_redirect(user.user_id)
    return jsonify({'success': True, 'redirect': redirect_url})


@auth_bp.route('/simple-register', methods=['POST'])
def simple_register():
    """Helyi fiók létrehozása Neon Auth nélkül"""
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'error': 'Töltse ki az összes mezőt.'}), 400

    if len(password) < 8:
        return jsonify({'error': 'A jelszónak legalább 8 karakteresnek kell lennie.'}), 400

    existing = User.find_by_email(email)
    if existing:
        return jsonify({'error': 'Ez az e-mail cím már foglalt.'}), 400

    try:
        user = User(
            username=name,
            email=email,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        auth_service = AuthService()
        auth_service.establish_session(user)
        session['auth_method'] = 'local'

        redirect_url = auth_service.resolve_post_auth_redirect(user.user_id)
        return jsonify({'success': True, 'redirect': redirect_url})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Regisztráció sikertelen. Kérjük, próbálja újra.'}), 500
