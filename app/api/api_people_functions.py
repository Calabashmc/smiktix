import os
import uuid  # For generating UUID to fill fs_uniquifier field
from flask import jsonify, request, url_for
from flask_security import current_user, login_required
from flask_security.utils import hash_password
import pandas as pd
import sqlalchemy as sa
from io import StringIO
from . import api_bp
from ..common.exception_handler import log_exception
from ..model import db

from ..common.fs_uniquifier import backfill_fs_uniquifier
from ..model.model_user import Department, Role, Team, User
from ..views.admin.form import AdminUserForm


def handle_user_params(stmt, params):
    """
    Handles filtering for User model based on 'params'.
    """
    p_name = params['name']
    p_name = p_name.replace('\n', ' ')

    teams = {
        team.name for team in
        db.session.execute(
            sa.select(Team)
        ).scalars()
    }

    departments = {
        department.name for department in
        db.session.execute(
            sa.select(Department)
        ).scalars()
    }
    account_status = {'active', 'inactive'}

    if p_name in teams:
        team = db.session.execute(
            sa.select(Team)
            .where(sa.and_(Team.name == p_name))
        ).scalar_one_or_none()

        if team:
            # Add additional filter to the query
            return stmt.where(User.team_id == team.id), f"Users in team '{p_name}'"
    elif p_name in departments:
        stmt = stmt.join(User.department).where(Department.department_name == p_name)
        return stmt, f"Users in department '{p_name}'"
    elif p_name in account_status:
        if p_name == 'Active':
            return stmt.where(User.active.is_(True)), 'Active users'
        elif p_name == 'Inactive':
            return stmt.where(User.active.is_(False)), 'Inactive users'
    else:
        return stmt, 'All users'

    return stmt


@api_bp.get('/people/get_requester_details/')
@api_bp.get('/people/get-current-user/')
@login_required
def get_current_user():
    """
    Get user details by query param (?id=) or return current user.
    """
    user_id = request.args.get('id', type=int) or current_user.id

    user = db.session.execute(
        sa.select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    avatar = url_for('static', filename=f'images/users/{user.avatar}')

    response = {
        'user_id': user.id,
        'avatar': avatar,
        'user_first_name': user.first_name,
        'user_last_name': user.last_name,
        'user_full_name': user.full_name,
        'user_username': user.username,
        'user_department_id': user.department_id,
        'user_team_id': user.team_id,
        'user_manager_id': user.manager_id,
        'user_occupation': user.occupation,
        'user_phone': user.phone,
        'user_email': user.email,
        'user_role_id': user.role_ids,  # @property in model
        'user_active': user.active or False
    }
    return jsonify(response)



def get_support_agents(team):
    team = db.session.execute(
        sa.select(Team)
        .where(Team.id == team)
    ).scalars().one_or_none()

    if not team:
        return [('', 'Select an active team first...')]

    if not team.members:
        return [('', 'Team has no members...')]

    # Add an empty option
    member_array = [('', 'Not yet assigned...')]

    for name in team.members:
        member_array.append((name.id, name.full_name))

    return member_array


@api_bp.get('/get_team_members/')
@login_required
def get_team_members():
    """
    Fetch team members to populate drop-down on change of Team SelectField. Change noticed by javascript
    support-agents.js
    :return: json 'members' and list of all members of the team selected
    """
    team = request.args.get('team')
    member_array = get_support_agents(team)
    return jsonify({'members': member_array})


@api_bp.post('/get-departments/')
@login_required
def get_departments():
    departments = db.paginate(sa.select(Department), page=1, per_page=10, error_out=False)
    response = {
        'last_page': departments.pages,
        'data': [{
            'id': department.id,
            'department_name': department.department_name,
            'description': department.description
        } for department in departments]
    }
    return jsonify(response)


@api_bp.post('/get_roles/')
@login_required
def get_roles():
    roles = db.paginate(sa.select(Role), page=1, per_page=10, error_out=False)
    response = {
        'last_page': roles.pages,
        'data': [{
            'id': role.id,
            'name': role.name,
            'description': role.description
        } for role in roles]
    }
    return jsonify(response)


@api_bp.get('/get_user_stats/')
@login_required
def get_user_stats():
    user = (db.session.execute(
        sa.select(User)
        .where(User.full_name == current_user.full_name)
    ).scalars().one_or_none())

    incident_count = user.get_incident_count()
    request_count = user.get_request_count()

    ideas_count = user.get_ideas_count()
    cis_owned_count = user.get_cis_owned_count()
    # ideas_proposed = user.get_ideas_proposed()
    # cis_owned_links = user.get_cis_owned()

    return jsonify(
        {'incidents': incident_count,
         'requests': request_count,
         'ideas': ideas_count,
         'devices': cis_owned_count
         }
    )


@api_bp.get('/get-orgchart-data/')
@login_required
def get_orgchart_data():
    subordinates = []
    data_source = {}
    user_id = request.args.get('id')

    user = db.session.execute(
        sa.select(User)
        .where(User.id == user_id)
    ).scalar_one_or_none()

    manager = db.session.execute(
        sa.select(User)
        .where(User.id == user.manager_id)
    ).scalar_one_or_none()

    children = db.session.execute(
        sa.select(User)
        .where(User.manager_id == user_id)
    ).scalars().all()

    for child in children:
        subordinate = {
            'name': child.full_name,
            'avatar': child.avatar,
            'title': child.occupation or 'no title',
            'email': child.email,
            'phone': child.phone,
            'relationship': 110  # Assuming all children have siblings and no parent
        }
        subordinates.append(subordinate)

    me = [
        {
            'name': user.full_name,
            'avatar': user.avatar,
            'title': user.occupation,
            'email': user.email,
            'phone': user.phone,
            'relationship': 110,
            'children': subordinates
        }
    ]

    data_source['id'] = 'rootNode'
    data_source['className'] = 'top-level'
    data_source['name'] = manager.full_name
    data_source['avatar'] = manager.avatar
    data_source['title'] = manager.occupation or 'manager'
    data_source['email'] = manager.email
    data_source['phone'] = manager.phone
    # Assuming the manager has children. '111' tells orgchart.js the depth
    # First character is whether current node has parent node;
    # Second character is whether current node has siblings nodes;
    # Third character is whether current node has children node.
    data_source['relationship'] = 111
    data_source['children'] = me

    return jsonify(data_source)


# these are for orgchart.js - not sure if I'll use. Probs not.
# @api_bp.get('/orgchart/children/<node_id>')
# def get_child_nodes(node_id):
#     # Retrieve and return children data for the specified node_id
#     # You may fetch this data from your data source (e.g., database)
#     # and convert it to JSON format
#     children_data = [...]  # Your logic to fetch children data
#     return jsonify(children_data)
#
#
# @api_bp.get('/orgchart/parent/<node_id>')
# def get_parent_nodes(node_id):
#     # Retrieve and return parent data for the specified node_id
#     # Similar to the 'get_children' route
#     parent_data = [...]  # Your logic to fetch parent data
#     return jsonify(parent_data)
#
#
# @api_bp.get('/orgchart/siblings/<node_id>')
# def get_sibling_nodes(node_id):
#     # Retrieve and return siblings data for the specified node_id
#     siblings_data = [...]  # Your logic to fetch siblings data
#     return jsonify(siblings_data)
#
#
# @api_bp.get('/orgchart/families/<node_id>')
# def get_family_nodes(node_id):
#     # Retrieve and return families data for the specified node_id
#     families_data = [...]  # Your logic to fetch families data
#     return jsonify(families_data)

@api_bp.get('/get_profile_details/')
@login_required
def get_profile_details():
    response = {}
    user_details = db.session.execute(
        sa.select(User)
        .where(User.full_name == current_user.full_name)
    ).scalar_one_or_none()

    response['avatar'] = url_for('static', filename=f'images/users/{user_details.avatar}')
    response['full_name'] = user_details.full_name
    response['first_name'] = user_details.first_name
    response['last_name'] = user_details.last_name
    response['phone'] = user_details.phone
    response['email'] = user_details.email
    response['department'] = user_details.department.name
    response['position'] = user_details.occupation
    response['my_team'] = user_details.team.name
    response['my_assets'] = user_details.owned_assets
    response['roles'] = user_details.role_names  # @property in model_user

    return jsonify(response)


@api_bp.post('/people/get-user-counts//')
@login_required
def get_user_counts():
    total_users = db.session.execute(sa.select(sa.func.count(User.id))).scalars().one_or_none()
    active_users = db.session.execute(sa.select(sa.func.count(User.id)).where(User.active == True)).scalar_one_or_none()
    inactive_users = db.session.execute(sa.select(sa.func.count(User.id)).where(User.active == False)).scalar_one_or_none()

    return jsonify({
        'All': total_users,
        'active': active_users,
        'inactive': inactive_users,
    })


@api_bp.post('/people/get-user-teams-counts/')
@login_required
def get_user_teams_counts():
    """
    This function retrieves team member counts and returns a JSON response.
    """
    # Use a query to join Team and User tables through TeamUser

    stmt = sa.select(Team.name, sa.func.count(User.id)). \
        outerjoin(User). \
        group_by(Team.name)

    # Execute the statement
    team_member_counts = db.session.execute(stmt).fetchall()

    result = {name: count for name, count in team_member_counts}
    # Return the JSON response
    return jsonify(result)


@api_bp.post('/people/get-user-departments-counts/')
@login_required
def get_user_departments_counts():
    departments = db.session.execute(
        sa.select(Department.name, sa.func.count(User.id))
        .outerjoin(User)
        .group_by(Department.name)
    ).fetchall()

    department_counts = {dpt: count for dpt, count in departments}
    return jsonify(department_counts)


@api_bp.post('/people/add-user/')
@login_required
def add_user():
    form = AdminUserForm()
    avatar = os.path.basename(form.avatar.data)

    if form.validate():
        user = db.session.execute(
            sa.select(User)
            .where(sa.and_(User.username == form.username.data))
        ).scalar_one_or_none()

        # If no existing record is found, initialize a new User instance
        if user is None:
            user = User()
            user.fs_uniquifier = str(uuid.uuid4())  # Generate a new fs_uniquifier for new users

        # Assign each field individually
        user.active = form.active.data
        user.avatar = avatar
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.full_name = f'{form.first_name.data} {form.last_name.data}'
        user.username = form.username.data

        # Hash the password before storing it
        # Only reset password if a new one is entered and matches confirmation
        if form.password.data and form.password.data.strip():
            if form.password.data.strip() != form.confirm_password.data.strip():
                return jsonify({'error': 'Passwords do not match'}), 400
            user.password = hash_password(form.password.data.strip())

        user.occupation = form.occupation.data
        user.phone = form.phone.data
        user.email = form.email.data
        user.manager_id = form.manager_id.data or None
        user.team_id = form.team_id.data
        user.department_id = form.department_id.data


        # Assign roles properly
        selected_role_ids = form.role_id.data  # This will be a list of IDs if it's a multiselect
        roles = db.session.execute(sa.select(Role).where(Role.id.in_(selected_role_ids))).scalars().all()
        user.roles = roles  # Replace existing roles with the selected ones

        try:
            db.session.merge(user)
            db.session.commit()
            return jsonify({'message': 'User added successfully'}), 201
        except Exception as e:
            log_exception(f'{e}')
            db.session.rollback()

            return jsonify({'error': 'Failed to add user', 'details': str(e)}), 500  # Internal Server Error
    else:
        error_messages = [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
        return jsonify({'error': 'Invalid form data', 'details': error_messages}), 400


@api_bp.post('/csv-user-import/')
@login_required
def csv_user_import():
    """
    Endpoint to import users from a CSV file using Pandas.
    :return: Import status or detailed error logs for failed rows.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No CSV file uploaded'}), 400

    csv_file = request.files['file']
    if not csv_file.filename.endswith('.csv'):
        return jsonify({'error': 'Invalid file type. Please upload a CSV file.'}), 400

    try:
        # Read CSV file using Pandas
        content = csv_file.stream.read().decode('utf-8')
        data = pd.read_csv(StringIO(content))

        # Validate required columns
        required_columns = ['username', 'email', 'first_name', 'last_name']
        if not all(column in data.columns for column in required_columns):
            return jsonify({'error': f"Missing required columns: {set(required_columns) - set(data.columns)}"}), 400

        import_errors = []

        # Iterate over rows for validation and saving
        for index, row in data.iterrows():
            try:
                # Validate row values
                if row[required_columns].isnull().any():
                    raise ValueError(f'Row {index + 1}: Missing required fields.')

                # Check if user exists
                user = db.session.execute(
                    sa.select(User).where(User.username == row['username'])
                ).scalar_one_or_none()

                if user is None:
                    user = User()
                    user.fs_uniquifier = str(uuid.uuid4())

                # Populate user fields
                user.username = row['username']
                user.email = row['email']
                user.first_name = row['first_name']
                user.last_name = row['last_name']
                user.full_name = f"{row['first_name']} {row['last_name']}"
                user.password = hash_password('welcome123!')  # Default password
                user.occupation = row.get('occupation', '')
                user.phone = row.get('phone', '')
                user.department_id = int(row.get('department_id', 0)) if 'department_id' in row else None
                user.team_id = int(row.get('team_id', 0)) if 'team_id' in row else None
                user.active = str(row.get('active', 'true')).lower() == 'true'

                # Assign roles
                if 'roles' in row and pd.notna(row['roles']):
                    role_names = row['roles'].split(',')
                else:
                    role_names = ['team member']  # Only set this if the "roles" key is missing or invalid

                # Query the roles after setting role_names correctly
                roles = db.session.execute(
                    sa.select(Role)
                    .where(Role.name.in_(role_names))
                ).scalars().all()

                user.roles = roles

                db.session.merge(user)
                db.session.commit()

            except Exception as e:
                db.session.rollback()
                log_exception(f'{e}')
                import_errors.append({'row': index + 1, 'error': str(e)})

        backfill_fs_uniquifier()

        if import_errors:
            return jsonify({'message': 'Import error: check your CSV formatting', 'errors': import_errors}), 400
        return jsonify({'message': 'All users imported successfully'}), 201

    except Exception as e:
        log_exception(f'{e}')
        return jsonify({'error': 'Failed to process CSV', 'details': str(e)}), 500

@api_bp.post('/people/update-avatar/')
@login_required
def update_avatar():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400
    user_id = data.get('user-id')
    avatar = data.get('avatar')

    if not user_id or not avatar:
        return jsonify({'error': 'Missing user ID or avatar URL'}), 400

    avatar = os.path.basename(avatar)
    user = db.session.execute(
        sa.select(User)
        .where(User.id == user_id)
    ).scalars().one_or_none()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.avatar = avatar
    try:
        db.session.commit()
        return jsonify({'message': 'Avatar updated successfully'}), 200
    except Exception as e:
        log_exception(f'{e}')
        return jsonify({'error': 'Failed to update avatar', 'details': str(e)}), 500
