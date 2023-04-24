import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.models import User, Project, Image, engine, async_engine
from app.utils.password_hash import set_password, password_check


logging.basicConfig(
    level=logging.INFO,
    filename='logs.log',
    filemode='a',
    format='[%(asctime)s] [%(levelname)s] [%(message)s]'
)

app = FastAPI(title='Save projects')

Session = sessionmaker(bind=engine)
async_session = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)


@app.post('/users/')
def create_user(name: str, password: str):
    """Эндпоинт, добавление или регистрация пользователя."""

    session = Session()
    user = User(name=name, password=set_password(password=password))
    session.add(user)
    session.commit()
    logging.info(f'User {name} create')

    return {'id': user.id, 'name': user.name}


@app.get('/users/{user_id}/')
async def read_user(user_id: int, password: str):
    """Эндпоинт, запрос детальной информации пользователя."""

    async with async_session() as session:
        user = await session.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail='Пользователя не существует.'
            )
        elif not password_check(
                pass_hash=user.password,
                password=password
        ):
            raise HTTPException(status_code=404, detail='Неверный пароль.')
        else:
            logging.info(
                f'User {user.name} requested '
                f'detailed information about yourself'
            )
            return {'username': user.name}


@app.put('/users/{user_id}/')
async def update_user(user_id: int, password: str, name: str):
    """
    Эндпоинт, запрос изменения информации пользователя.
    """

    async with async_session() as session:
        user = await session.get(User, user_id)

        if not user:
            raise HTTPException(status_code=404,
                                detail='Пользователя не существует.')
        elif not password_check(pass_hash=user.password, password=password):
            raise HTTPException(status_code=404, detail='Неверный пароль.')
        else:
            user.name = name
            await session.commit()
            logging.info(f'User {user.name} changed your information')
            return {'id': user.id, 'name': user.name}


@app.delete('/users/{user_id}/')
async def delete_user(user_id: int, password: str):
    """Эндпоинт, запрос удалений пользователя."""

    async with async_session() as session:
        user = await session.get(User, user_id)

        if not user:
            raise HTTPException(status_code=404,
                                detail='Пользователя не существует.')
        elif not password_check(pass_hash=user.password, password=password):
            raise HTTPException(status_code=404, detail='Неверный пароль.')
        else:
            await session.delete(user)
            await session.commit()
            logging.info(f'User {user.name} deleted')
            return {'message': 'Пользователь удалён.'}


@app.post('/users/{user_id}/projects/')
def create_project(user_id: int, name: str):
    """Эндпоинт, добавление проекта."""

    session = Session()
    user = session.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404,
                            detail='Пользователя не существует.')

    project = Project(name=name, user=user)
    session.add(project)
    session.commit()
    logging.info(f'User {user.name} create project')
    return {'id': project.id, 'name': project.name, 'user_id': project.user_id}


@app.get('/users/{user_id}/projects/')
async def read_project(user_id: int, password: str):
    """Эндпоинт, запрос детальной информации проектов пользователя."""
    session = Session()

    user = session.query(User).get(user_id)
    projects = session.query(Project).filter_by(user_id=user_id).all()

    if not user:
        raise HTTPException(status_code=404,
                            detail='Пользователя не существует.')
    elif not password_check(pass_hash=user.password, password=password):
        raise HTTPException(status_code=404, detail='Неверный пароль.')
    elif not projects:
        raise HTTPException(status_code=404, detail='Проектов нет.')
    else:
        if len(projects) > 1:
            result = list()
            for project in projects:
                result.append(
                    {
                        'user_id': project.user_id,
                        'project_name': project.name,
                        'project_id': project.id
                    }
                )
            logging.info(
                f'User {user.name} requested '
                f'information about projects'
            )
            return result
        else:
            logging.info(
                f'User {user.name} requested '
                f'information about projects'
            )
            return projects


@app.put('/users/{user_id}/projects/{project_id}/')
async def update_project(
        user_id: int,
        password: str,
        project_id: str,
        project_name: str
):
    """Эндпоинт, запрос изменения информации о проекте пользователя."""

    session = Session()

    user = session.query(User).get(user_id)
    project = session.query(Project).get(project_id)

    if not user:
        raise HTTPException(status_code=404,
                            detail='Пользователя не существует.')
    elif not password_check(pass_hash=user.password, password=password):
        raise HTTPException(status_code=404, detail='Неверный пароль.')
    elif not project:
        raise HTTPException(status_code=404, detail='Проектa c таким id нет.')
    else:
        if user.id == project.user_id:
            project.name = project_name
            session.commit()
            logging.info(
                f'User {user.name} changed '
                f'the project {project.name}'
            )
            return {'project_id': project.id, 'project_name': project.name}
        else:
            raise HTTPException(status_code=404,
                                detail='Проект не принадлежит пользователю.')


@app.delete('/users/{user_id}/projects/{project_id}/')
async def delete_project(user_id: int, password: str, project_id: str):
    """Эндпоинт, запрос удаление проекта пользователя."""

    session = Session()

    user = session.query(User).get(user_id)
    project = session.query(Project).get(project_id)

    if not user:
        raise HTTPException(status_code=404,
                            detail='Пользователя не существует.')
    elif not password_check(pass_hash=user.password, password=password):
        raise HTTPException(status_code=404, detail='Неверный пароль.')
    elif not project:
        raise HTTPException(status_code=404, detail='Проектa c таким id нет.')
    else:
        if user.id == project.user_id:
            session.delete(project)
            session.commit()
            logging.info(
                f'User {user.name} deleted '
                f'the project {project.name}'
            )
            return {'message': f'Проект c id({project_id}) удалён.'}
        else:
            raise HTTPException(status_code=404,
                                detail='Проект не принадлежит пользователю.')


@app.post('/users/{user_id}/projects/{project_id}/images/')
async def add_image(
        user_id: int,
        password: str,
        project_id: int,
        file: UploadFile = File(...)
):
    """Эндпоинт, добавление изображения к проекту."""
    list_format = ['PNG', 'JPEG', 'JPG', 'GIF', 'RAW', 'TIFF', 'BMP', 'PSD']

    session = Session()

    user = session.query(User).get(user_id)
    project = session.query(Project).get(project_id)

    if not user:
        raise HTTPException(status_code=404,
                            detail='Пользователя не существует.')
    elif not password_check(pass_hash=user.password, password=password):
        raise HTTPException(status_code=404, detail='Неверный пароль.')
    elif file.filename.upper().split('.')[-1] not in list_format:
        raise HTTPException(status_code=404, detail='Неверный формат файла.')
    elif not project:
        raise HTTPException(status_code=404, detail='Проекта не существует.')

    else:
        if user.id == project.user_id:
            dest_path = Path('static/project_images/') / file.filename
            contents = await file.read()
            with open(dest_path, 'wb') as f:
                f.write(contents)
            image = Image(image_url=str(dest_path), project=project)
            session.add(image)
            session.commit()
            logging.info(
                f'User {user.name} add '
                f'image in project {project.name}'
            )
            return {
                'id': image.id,
                'name': image.image_url,
                'project_id': image.project_id
            }
        else:
            raise HTTPException(status_code=404,
                                detail='Проект не принадлежит пользователю.')


@app.get('/users/{user_id}/projects/{project_id}/images/')
async def read_image(user_id: int, password: str,  project_id: int):
    """Эндпоинт, получение изображений к проекту."""

    session = Session()

    user = session.query(User).get(user_id)
    project = session.query(Project).get(project_id)
    image = session.query(Image).join(Project).filter(Project.user == user)
    print(image)

    if not user:
        raise HTTPException(status_code=404,
                            detail='Пользователя не существует.')
    elif not password_check(pass_hash=user.password, password=password):
        raise HTTPException(status_code=404, detail='Неверный пароль.')
    elif not project:
        raise HTTPException(status_code=404, detail='Проекта не существует.')

    else:
        if user.id == project.user_id:
            result = list()
            for img in image:
                result.append(
                    {
                        'id': img.id,
                        'url': img.image_url,
                        'project_id': img.project_id
                    }
                )
            logging.info(
                f'User {user.name} '
                f'get info for images in project {project.name}'
            )
            return result
        else:
            raise HTTPException(status_code=404,
                                detail='Проект не принадлежит пользователю.')


@app.delete('/users/{user_id}/projects/{project_id}/images/{image_id}/')
async def delete_image(
        user_id: int,
        password: str,
        project_id: int,
        image_id: int
):
    """Эндпоинт, удаление изображений к проекту."""

    session = Session()

    user = session.query(User).get(user_id)
    project = session.query(Project).get(project_id)
    image = session.query(Image).get(image_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail='Пользователя не существует.'
        )
    elif not password_check(pass_hash=user.password, password=password):
        raise HTTPException(status_code=404, detail='Неверный пароль.')
    elif not project:
        raise HTTPException(status_code=404, detail='Проекта не существует.')
    elif not image:
        raise HTTPException(status_code=404,
                            detail='Изображения не существует.')

    else:
        if user.id == project.user_id and image.project_id == project.id:
            session.delete(image)
            session.commit()
            logging.info(
                f'User {user.name} '
                f'delete image({image.id}) '
                f'in project {project.name}'
            )
            return {'message': 'Изображение удалено'}
        else:
            raise HTTPException(
                status_code=404,
                detail='Проект не принадлежит пользователю.'
            )


@app.get('/users/{user_id}/stats/')
def get_stats(user_id: int, password: str):
    """Эндпоинт, получение количества проектов у пользователя."""

    session = Session()
    user = session.query(User).get(user_id)

    if not user:
        raise HTTPException(status_code=404,
                            detail='Пользователя не существует.')
    elif not password_check(pass_hash=user.password, password=password):
        raise HTTPException(status_code=404, detail='Неверный пароль.')
    else:
        project_count = session.query(Project).filter_by(user=user).count()
        image_count = session.query(Image).\
            join(Project).\
            filter(Project.user == user).\
            count()
        logging.info(
            f'User {user.name} view the number '
            f'of projects and images owned by a user'
        )
        return {
            'user_id': user.id,
            'project_count': project_count,
            'image_count': image_count
        }
