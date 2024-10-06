import discord
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, TextInput

# 메시지 콘텐츠 인텐트를 포함하여 Intents 생성
intents = discord.Intents.default()
intents.messages = True  # 메시지 관련 인텐트 활성화
intents.message_content = True  # 메시지 콘텐츠 인텐트 활성화

bot = commands.Bot(command_prefix='!', intents=intents)

# 운영자 역할 이름 설정
ADMIN_ROLE_NAME = "운영자"

@bot.event
async def on_ready():
    print('다음으로 로그인합니다: ')
    print(bot.user.name)
    print('connection was successful')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("하고 싶은거 적어주세요 :)"))

@bot.command()
@commands.has_role(ADMIN_ROLE_NAME)
async def dropdown(ctx):
    select = Select(
        placeholder="📋️ 문의할 항목을 선택하세요",
        options=[
            discord.SelectOption(emoji="❗", label="서버건의", description="서버에 생겼으면 하는 것을 문의해주세요."),
            discord.SelectOption(emoji="🔄", label="기타", description="기타 문의 사항입니다.")
        ]
    )

    async def my_callback(interaction):
        if select.values[0] == "서버건의":
            await create_suggestion_channel(ctx)
        elif select.values[0] == "기타":
            await create_suggestion_channel(ctx)

    select.callback = my_callback

    view = View()
    view.add_item(select)

    # Embed 메시지 전송
    embed = discord.Embed(title="📮ㆍ문의 메뉴", description="신고,질문,건의 등 자신의 카테고리에 맞는 선택을 해주세요.", color=discord.Color.green())
    embed.set_image(url="https://postfiles.pstatic.net/MjAyNDEwMDdfNSAg/MDAxNzI4MjM3MTk4MDk4.qKN3GfqJbfXpEaMQLjJNToabTLYUL0_fhHU4_h5IWAMg.hQhRBrPZAhhonIIvtRwnoKbYTc2dXhMIiSFQmSJpd2Ag.PNG/%F0%9F%93%8B.png?type=w966")
    await ctx.send(embed=embed, view=view)

# 서버 건의 채널 생성 함수
async def create_suggestion_channel(ctx):
    try:
        guild = ctx.guild
        member = ctx.author

        # 운영자 역할 찾기
        admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)

        # 이미 존재하는 건의 채널 수 찾기
        existing_channels = [channel for channel in guild.channels if channel.name.startswith('문의-')]
        channel_number = len(existing_channels) + 1  # 건의 채널 번호 생성

        # 새로운 건의 채널 이름 생성
        new_channel_name = f"문의-{channel_number:04d}"

        # 채널 생성 및 권한 설정
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),  # 모든 사용자에게 채널 숨기기
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True),  # 건의한 사용자에게만 보기/쓰기 권한 부여
            admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)  # 운영자에게 보기/쓰기 권한 부여
        }

        # 채널 생성
        new_channel = await guild.create_text_channel(new_channel_name, overwrites=overwrites)

        # Embed 메시지 생성
        embed = discord.Embed(title="문의", description="여기에 문의를 남겨주세요.", color=discord.Color.green())
        await new_channel.send(embed=embed)

        # 이미지 URL 입력을 위한 메시지 추가
        await new_channel.send("건의 사항과 함께 이미지를 첨부하고 싶으시면 URL을 입력해주세요.")

        # 문의 닫기 버튼 추가
        close_button = Button(label="문의 닫기", style=discord.ButtonStyle.red)

        async def close_ticket_callback(interaction):
            # 더블 체크를 위한 메시지 전송
            await interaction.response.send_message("문의 닫기를 정말 원하십니까?", ephemeral=True)
            confirm_view = View(timeout=None)

            # "문의 닫기" 확인 버튼
            confirm_button = Button(label="문의 닫기", style=discord.ButtonStyle.red)
            async def confirm_callback(interaction):
                await new_channel.send("문의가 닫혔습니다.")
                await new_channel.delete()  # 채널 삭제
                await interaction.response.send_message("문의가 닫혔습니다.", ephemeral=True)

            confirm_button.callback = confirm_callback
            confirm_view.add_item(confirm_button)

            # "문의 다시 열기" 버튼
            reopen_button = Button(label="문의 다시 열기", style=discord.ButtonStyle.green)
            async def reopen_callback(interaction):
                await new_channel.send("문의가 다시 열렸습니다.")  # 메시지로 알림
                await interaction.response.send_message("문의가 다시 열렸습니다.", ephemeral=True)

                # 채널 권한 복원 (운영자 및 사용자 권한 재설정)
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),  # 모든 사용자에게 채널 숨기기
                    member: discord.PermissionOverwrite(view_channel=True, send_messages=True),  # 건의한 사용자에게만 보기/쓰기 권한 부여
                    admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)  # 운영자에게 보기/쓰기 권한 부여
                }
                await new_channel.set_permissions(guild.default_role, view_channel=False)
                await new_channel.set_permissions(member, view_channel=True, send_messages=True)
                await new_channel.set_permissions(admin_role, view_channel=True, send_messages=True)

            reopen_button.callback = reopen_callback
            confirm_view.add_item(reopen_button)

            await interaction.followup.send(view=confirm_view)  # 확인 버튼 전송

        close_button.callback = close_ticket_callback

        # 닫기 버튼을 포함하는 View 생성
        close_view = View()
        close_view.add_item(close_button)

        await new_channel.send(view=close_view)  # 닫기 버튼 전송

    except Exception as e:
        await ctx.send(f"채널 생성 중 오류가 발생했습니다: {e}")

bot.run('MTI5MjE5NzA1NjE5ODM0ODkzNA.G_97NS.J6GwB5Temp6DJVqsu503rijbyxkNif_MYhxorA')